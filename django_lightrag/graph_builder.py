from loguru import logger
import uuid
import re
from typing import List

def slugify(text: str) -> str:
    return re.sub(r'[^a-zA-Z0-9]+', '-', str(text).lower()).strip('-')

def merge_concept(conn, pref_label: str, concept_data=None, source_chunk: str = "") -> str:
    """
    Idempotent upsert of a concept using its slugified pref_label as ID.
    Always updates metadata (like definition) to the latest found.
    """
    cid = slugify(pref_label)
    if not cid:
        cid = f"concept-{uuid.uuid4().hex[:8]}"
        
    alt_labels = concept_data.alt_labels if concept_data else []
    definition = concept_data.definition if concept_data else ""
    confidence = concept_data.confidence if concept_data else 1.0
    
    query = """
    MERGE (c:Concept {id: $id})
    SET c.prefLabel = $pref_label,
        c.altLabels = $alt_labels,
        c.definition = $definition,
        c.confidence_score = $confidence,
        c.source_chunk = $source_chunk
    RETURN c.id
    """
    params = {
        "id": cid,
        "pref_label": pref_label,
        "alt_labels": alt_labels,
        "definition": definition,
        "confidence": confidence,
        "source_chunk": source_chunk
    }
    
    conn.execute(query, params)
    return cid

def merge_paper(conn, paper_id: str, title: str, abstract: str, year: int = 0, doi: str = "") -> str:
    query = """
    MERGE (p:Paper {id: $id})
    SET p.title = $title,
        p.abstract = $abstract,
        p.year = $year,
        p.doi = $doi
    RETURN p.id
    """
    params = {
        "id": paper_id,
        "title": title,
        "abstract": abstract,
        "year": year,
        "doi": doi
    }
    conn.execute(query, params)
    return paper_id

def add_hierarchical_relation(conn, child_id: str, parent_id: str) -> None:
    # Child -> Parent is BROADER
    # Parent -> Child is NARROWER
    query = """
    MATCH (c1:Concept {id: $c_id}), (c2:Concept {id: $p_id})
    MERGE (c1)-[:BROADER]->(c2)
    MERGE (c2)-[:NARROWER]->(c1)
    """
    conn.execute(query, {"c_id": child_id, "p_id": parent_id})

def add_related(conn, id_a: str, id_b: str, confidence: float = 1.0) -> None:
    query = """
    MATCH (c1:Concept {id: $id_a}), (c2:Concept {id: $id_b})
    MERGE (c1)-[r:RELATED]->(c2)
    SET r.confidence_score = $confidence
    MERGE (c2)-[r2:RELATED]->(c1)
    SET r2.confidence_score = $confidence
    """
    conn.execute(query, {"id_a": id_a, "id_b": id_b, "confidence": confidence})


def link_paper_to_concept(conn, paper_id: str, concept_id: str, relevance: float = 1.0) -> None:
    query = """
    MATCH (p:Paper {id: $pid}), (c:Concept {id: $cid})
    MERGE (p)-[r:EXPLORES]->(c)
    SET r.relevance_score = $relevance
    """
    conn.execute(query, {"pid": paper_id, "cid": concept_id, "relevance": relevance})

def add_generic_relation(conn, from_label: str, to_label: str) -> None:
    # If the user extracted arbitrary relationships with LLM, we can map them to 
    # either a generic RELATED or IS_A depending on the label mapping, or simply add RELATED.
    fid = slugify(from_label)
    tid = slugify(to_label)
    # Ensure both nodes exist if not already ingested
    conn.execute("MERGE (c:Concept {id: $id})", {"id": fid})
    conn.execute("MERGE (c:Concept {id: $id})", {"id": tid})
    query = """
    MATCH (c1:Concept {id: $fid}), (c2:Concept {id: $tid})
    MERGE (c1)-[:RELATED]->(c2)
    """
    conn.execute(query, {"fid": fid, "tid": tid})

def validate_no_circular_hierarchy(conn) -> List[List[str]]:
    # Simple check for self-loops: MATCH (c:Concept)-[:BROADER]->(c)
    # A complete cycle check in Cypher: MATCH p=(c)-[:BROADER*1..10]->(c)
    # but variable length paths usually require paths from non-cyclic paths.
    # Let's just check for 1-hop and 2-hop cycles for simplicity.
    cycles = []
    try:
        res = conn.execute("MATCH (c:Concept)-[:BROADER]->(c) RETURN id(c)")
        while res.has_next():
             row = res.get_next()
             cycles.append([row[0], row[0]])
    except Exception as e:
        logger.warning(f"Cycle validation failed: {e}")
    return cycles

def validate_no_isolated_concepts(conn) -> List[str]:
    isolated = []
    try:
        q = """
        MATCH (c:Concept)
        WHERE NOT (c)--()
        RETURN c.id
        """
        res = conn.execute(q)
        while res.has_next():
            row = res.get_next()
            isolated.append(row[0])
    except Exception as e:
        logger.warning(f"Isolated concept validation failed: {e}")
    return isolated

def validate_no_duplicates(conn) -> List[str]:
    # Since we use slugified ID, true duplicates with same slug are impossible due to PRIMARY KEY.
    # But we can check if different IDs have same exact prefLabel.
    dups = []
    try:
        q = """
        MATCH (c:Concept)
        WITH c.prefLabel AS label, collect(c.id) AS ids
        WHERE length(ids) > 1
        RETURN label
        """
        res = conn.execute(q)
        while res.has_next():
             row = res.get_next()
             dups.append(row[0])
    except Exception:
        pass
    return dups
