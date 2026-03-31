from loguru import logger
from .entity_extraction import extract_concepts_and_relations
from .graph_builder import (
    merge_concept,
    add_hierarchical_relation,
    add_generic_relation,
)
from .storage import get_ladybug_connection, get_concepts_collection
from .models import IngestLog
from .query_engine import _get_embedding


def ingest_text_chunk(text: str, source_id: str) -> IngestLog:
    """
    1. Call entity_extraction.extract_concepts_and_relations(text)
    2. For each concept: graph_builder.merge_concept() → get/create id
    3. Embed each concept text via litellm (LMStudio, text-embedding-ada-002)
       → upsert into ChromaDB 'concepts' collection
    4. Build all SKOS relationships in LadybugDB
    5. Write IngestLog to Django ORM
    6. Return IngestLog
    """
    log = IngestLog(source_id=source_id, source_text=text, status="processing")
    log.save()

    try:
        # Step 1: Extraction
        extracted_graph = extract_concepts_and_relations(text)

        # Keep track of generated IDs for linking
        label_to_id = {}

        conn = get_ladybug_connection()
        concepts_coll = get_concepts_collection()

        # Step 2 & 3: Upsert Concepts and generate embeddings
        for ext_concept in extracted_graph.concepts:
            # Merge into graph
            cid = merge_concept(
                conn, ext_concept.pref_label, ext_concept, source_chunk=text
            )
            label_to_id[ext_concept.pref_label.lower()] = cid

            # Embed mapping: We'll construct a text combining label and definition for semantic search
            embed_text = f"Concept: {ext_concept.pref_label}. Definition: {ext_concept.definition}"
            embedding = _get_embedding(embed_text)

            if embedding:
                # Upsert to ChromaDB
                metadata = {
                    "prefLabel": ext_concept.pref_label,
                    "definition": ext_concept.definition,
                }
                # Sanitize metadata (Chroma requires str, int, float, bool)
                metadata = {k: str(v) for k, v in metadata.items() if v is not None}

                concepts_coll.upsert(
                    ids=[cid],
                    embeddings=[embedding],
                    metadatas=[metadata],
                    documents=[embed_text],
                )

        # Step 4: Build SKOS Relationships
        # Hierarchies
        for ext_concept in extracted_graph.concepts:
            cid = label_to_id.get(ext_concept.pref_label.lower())
            if not cid:
                continue

            for broader_label in ext_concept.broader_than:
                p_id = label_to_id.get(broader_label.lower())
                if p_id:
                    add_hierarchical_relation(conn, child_id=cid, parent_id=p_id)
            for narrower_label in ext_concept.narrower_than:
                c_id = label_to_id.get(narrower_label.lower())
                if c_id:
                    add_hierarchical_relation(conn, child_id=c_id, parent_id=cid)
            for related_label in ext_concept.related_to:
                r_id = label_to_id.get(related_label.lower())
                if r_id:
                    # Handled broadly by generic/associative relations inside builder
                    add_generic_relation(conn, ext_concept.pref_label, related_label)

        # Generic relationships
        for sub_label, pred_label, obj_label in extracted_graph.relations:
            # For this MVP, we map structured Triples as RELATED edges or just generic relations
            # Wait, `add_generic_relation` MERGEs nodes if not exist.
            add_generic_relation(conn, sub_label, obj_label)

        # Step 5: Finalize Log
        log.concepts_extracted = len(extracted_graph.concepts)
        log.relations_extracted = len(extracted_graph.relations)
        log.status = "success"
        log.save()

    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        log.status = "error"
        log.error_message = str(e)
        log.save()

    return log
