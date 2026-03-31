from loguru import logger
import real_ladybug as lb
import chromadb
from django.conf import settings

_lbug_db = None
_lbug_conn = None


def get_ladybug_connection():
    global _lbug_db, _lbug_conn
    if _lbug_db is None:
        _lbug_db = lb.Database(settings.LADYBUG_DB_PATH)
        _lbug_conn = lb.Connection(_lbug_db)
    return _lbug_conn


_chroma_client = None


def get_chroma_client():
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(path=str(settings.CHROMADB_PATH))
    return _chroma_client


def get_concepts_collection():
    client = get_chroma_client()
    return client.get_or_create_collection(
        name="concepts", metadata={"hnsw:space": "cosine"}
    )


def get_papers_collection():
    client = get_chroma_client()
    return client.get_or_create_collection(
        name="papers", metadata={"hnsw:space": "cosine"}
    )


def init_ladybug_schema():
    conn = get_ladybug_connection()
    ddl_statements = [
        "CREATE NODE TABLE Concept(id STRING PRIMARY KEY, prefLabel STRING, altLabels STRING[], definition STRING, scopeNote STRING, source_chunk STRING, confidence_score DOUBLE, created_at STRING);",
        "CREATE NODE TABLE Paper(id STRING PRIMARY KEY, title STRING, abstract STRING, authors STRING[], year INT64, doi STRING, ingested_at STRING);",
        "CREATE NODE TABLE Author(id STRING PRIMARY KEY, name STRING, affiliation STRING);",
        "CREATE REL TABLE BROADER(FROM Concept TO Concept);",
        "CREATE REL TABLE NARROWER(FROM Concept TO Concept);",
        "CREATE REL TABLE RELATED(FROM Concept TO Concept, confidence_score DOUBLE, discovery_date STRING);",
        "CREATE REL TABLE EXPLORES(FROM Paper TO Concept, relevance_score DOUBLE, mention_count INT64);",
        "CREATE REL TABLE INTRODUCES(FROM Paper TO Concept);",
        "CREATE REL TABLE AUTHORED_BY(FROM Paper TO Author, role STRING);",
        "CREATE REL TABLE IS_A(FROM Concept TO Concept);",
        "CREATE REL TABLE HAS_PART(FROM Concept TO Concept);",
    ]
    for stmt in ddl_statements:
        try:
            conn.execute(stmt)
            logger.info(f"Executed: {stmt.split('(')[0]}")
        except Exception as e:
            if (
                "catalog exception" in str(e).lower()
                or "already exists" in str(e).lower()
            ):
                pass  # Ignore already exists errors
            else:
                logger.error(f"Error executing {stmt}: {e}")
                raise
