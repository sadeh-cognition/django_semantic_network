from loguru import logger
from django.shortcuts import get_object_or_404
from ninja import Router

from .schemas import (
    IngestRequest, IngestResponse, SearchRequest, SearchResult, ConceptOut, 
    GraphRAGRequest, GraphRAGResponse, TraversalRequest, ValidationReport
)
from .core import ingest_text_chunk
from .query_engine import faceted_search, bfs_traversal, graphrag_query, _concept_row_to_out
from .storage import get_ladybug_connection
from .graph_builder import validate_no_circular_hierarchy, validate_no_duplicates, validate_no_isolated_concepts

router = Router()

@router.post("/ingest", response=IngestResponse)
def ingest(request, payload: IngestRequest):
    logger.info(f"Ingesting source: {payload.source_id}")
    log = ingest_text_chunk(
        text=payload.text,
        source_id=payload.source_id
    )
    return IngestResponse(
        source_id=log.source_id,
        concepts_extracted=log.concepts_extracted,
        relations_extracted=log.relations_extracted,
        status=log.status
    )

@router.post("/search", response=SearchResult)
def search(request, payload: SearchRequest):
    res = faceted_search(query=payload.query, filters=payload.filters, top_k=payload.top_k)
    return res

@router.get("/concept/{concept_id}", response=ConceptOut)
def get_concept(request, concept_id: str):
    conn = get_ladybug_connection()
    q = "MATCH (c:Concept) WHERE c.id = $id RETURN c.id, c.prefLabel, c.altLabels, c.definition, c.confidence_score"
    res = conn.execute(q, {"id": concept_id})
    if res.has_next():
        cols = res.get_column_names()
        row = res.get_next()
        data = _concept_row_to_out(cols, row)
        return ConceptOut(**data)
    # Ninja handles exceptions natively or we can return 404 manually by throwing
    from ninja.errors import HttpError
    raise HttpError(404, "Concept not found")

@router.post("/graphrag", response=GraphRAGResponse)
def graphrag(request, payload: GraphRAGRequest):
    return graphrag_query(query=payload.natural_language_query, top_k=payload.top_k)

@router.post("/graph/traverse", response=list[dict])
def traverse(request, payload: TraversalRequest):
    return bfs_traversal(
        start_id=payload.start_concept_id,
        max_depth=payload.max_depth,
        direction=payload.direction
    )

@router.get("/validate", response=ValidationReport)
def validate(request):
    conn = get_ladybug_connection()
    isolated = validate_no_isolated_concepts(conn)
    circular = validate_no_circular_hierarchy(conn)
    duplicates = validate_no_duplicates(conn)
    
    is_valid = len(isolated) == 0 and len(circular) == 0 and len(duplicates) == 0
    return ValidationReport(
        isolated_concepts=isolated,
        circular_hierarchies=circular,
        duplicate_labels=duplicates,
        is_valid=is_valid
    )

@router.get("/analytics/pagerank", response=list[dict])
def pagerank(request):
    conn = get_ladybug_connection()
    results = []
    # Using LadybugDB's page rank extension, assuming it's loaded 
    # Or just returning dummy metrics for MVP since native PageRank syntax 
    # via extension might require specific syntax like: CALL Page_Rank('Concept') YIELD node, score
    try:
         q = "CALL Page_Rank('Concept') YIELD node, score RETURN node.id, score"
         res = conn.execute(q)
         while res.has_next():
             row = res.get_next()
             results.append({"id": row[0], "score": row[1]})
    except Exception as e:
         logger.warning(f"PageRank failed or not installed: {e}")
    return results
