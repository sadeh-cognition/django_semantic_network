from loguru import logger
import os
from typing import List, Dict, Any
import litellm

# Let's import our schemas and storage
from .schemas import SearchResult, ConceptOut, GraphRAGResponse
from .storage import get_ladybug_connection, get_concepts_collection, get_papers_collection


def _get_embedding(text: str) -> List[float]:
    model = os.environ.get("LMSTUDIO_EMBEDDING_MODEL", "text-embedding-ada-002")
    api_base = os.environ.get("LMSTUDIO_API_BASE", "http://localhost:1234/v1")
    try:
        response = litellm.embedding(
            model=model,
            api_base=api_base,
            input=[text]
        )
        return response.data[0]["embedding"]
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        return []

def _concept_row_to_out(cols: List[str], row: List[Any]) -> dict:
    # LadybugDB usually returns tuples/lists of values, we need to map to columns
    # Let's assume we queried RETURN c.id, c.prefLabel, c.altLabels, c.definition, c.confidence_score
    # Wait, Kuzu query response exposes get_column_names()
    d = dict(zip(cols, row))
    return {
        "id": d.get("c.id") or d.get("id", ""),
        "pref_label": d.get("c.prefLabel") or d.get("prefLabel", ""),
        "alt_labels": d.get("c.altLabels") or d.get("altLabels", []),
        "definition": d.get("c.definition") or d.get("definition", ""),
        "confidence_score": d.get("c.confidence_score") or d.get("confidence_score", 1.0)
    }


def faceted_search(query: str, filters: dict, top_k: int) -> SearchResult:
    """Combines Chroma semantic search with graph retrieval."""
    concepts_coll = get_concepts_collection()
    
    # 1. Semantic search if query provided
    concept_ids = set()
    if query:
        emb = _get_embedding(query)
        if emb:
            res = concepts_coll.query(
                query_embeddings=[emb],
                n_results=top_k,
                # filters could be applied to Chroma metadata here if necessary
                where=filters if filters else None
            )
            if res and res["ids"]:
                for cid in res["ids"][0]:
                    concept_ids.add(cid)
    
    # 2. Fetch full nodes from LadybugDB
    conn = get_ladybug_connection()
    concepts = []
    if concept_ids:
        # Array param in Kuzu: WHERE c.id IN $ids
        q = "MATCH (c:Concept) WHERE c.id IN $ids RETURN c.id, c.prefLabel, c.altLabels, c.definition, c.confidence_score"
        try:
            res = conn.execute(q, {"ids": list(concept_ids)})
            cols = res.get_column_names()
            while res.has_next():
                r = res.get_next()
                data = _concept_row_to_out(cols, r)
                concepts.append(ConceptOut(**data))
        except Exception as e:
            logger.error(f"Failed to fetch concepts from graph: {e}")

    return SearchResult(concepts=concepts, papers=[])


def bfs_traversal(start_id: str, max_depth: int, direction: str) -> List[dict]:
    conn = get_ladybug_connection()
    # Kuzu doesn't have `*1..3` syntax exactly like Neo4j, or maybe it does inline paths
    # Kuzu 0.5+ supports recursive joins `-[e:BROADER*1..3]->`
    
    # Let's map direction
    rel_type = "BROADER|NARROWER|RELATED"
    if direction == "broader":
        rel_type = "BROADER"
    elif direction == "narrower":
        rel_type = "NARROWER"
        
    query = f"""
    MATCH (s:Concept {{id: $id}})-[e:{rel_type}*1..{max_depth}]-(t:Concept)
    RETURN t.id, t.prefLabel, length(e) as depth
    """
    results = []
    try:
         res = conn.execute(query, {"id": start_id})
         cols = res.get_column_names()
         while res.has_next():
             row = res.get_next()
             d = dict(zip(cols, row))
             results.append({"id": d["t.id"], "pref_label": d["t.prefLabel"], "depth": d["depth"]})
    except Exception as e:
         logger.error(f"BFS traversal failed: {e}")
         
    return results

def graphrag_query(query: str, top_k: int) -> GraphRAGResponse:
    # 1. Semantic search for entry concepts
    search_res = faceted_search(query=query, filters={}, top_k=top_k)
    concepts = search_res.concepts
    
    # 2. Expand context (1-hop)
    context_str = ""
    target_ids = [c.id for c in concepts]
    
    if target_ids:
         conn = get_ladybug_connection()
         q = """
         MATCH (c:Concept)-[r:BROADER|NARROWER|RELATED]->(t:Concept)
         WHERE c.id IN $ids
         RETURN c.prefLabel, type(r), t.prefLabel, c.definition
         LIMIT 50
         """
         try:
             res = conn.execute(q, {"ids": target_ids})
             while res.has_next():
                 row = res.get_next()
                 context_str += f"- {row[0]} [is {row[1]}] {row[2]}. (Definition of {row[0]}: {row[3]})\n"
         except Exception as e:
             logger.error(f"Graph context expansion failed: {e}")
             
    # 3. Call LLM to ground response
    model = os.environ.get("LLM_MODEL", "groq/llama-3.1-8b-instant")
    system_prompt = (
        "You are an AI assistant answering questions grounded in a provided knowledge graph context.\n"
        "Use ONLY the following relationships and definitions to answer the question.\n"
        "Context:\n"
    ) + context_str
    
    try:
        response = litellm.completion(
             model=model,
             messages=[
                 {"role": "system", "content": system_prompt},
                 {"role": "user", "content": query}
             ],
             temperature=0.0
        )
        answer = response.choices[0].message.content
    except Exception as e:
        logger.error(f"GraphRAG inference failed: {e}")
        answer = "I'm sorry, I encountered an error while generating the response."
        
    return GraphRAGResponse(
         answer=answer,
         grounding_concepts=concepts,
         cypher_context=context_str
    )
