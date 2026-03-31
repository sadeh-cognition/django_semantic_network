from pydantic import BaseModel
from typing import List, Dict


class IngestRequest(BaseModel):
    text: str
    source_id: str


class IngestResponse(BaseModel):
    source_id: str
    concepts_extracted: int
    relations_extracted: int
    status: str


class ConceptOut(BaseModel):
    id: str
    pref_label: str
    alt_labels: List[str]
    definition: str
    confidence_score: float


class SearchRequest(BaseModel):
    query: str
    filters: Dict[str, str] = {}
    top_k: int = 10


class SearchResult(BaseModel):
    concepts: List[ConceptOut]
    papers: List[dict]


class GraphRAGRequest(BaseModel):
    natural_language_query: str
    top_k: int = 5


class GraphRAGResponse(BaseModel):
    answer: str
    grounding_concepts: List[ConceptOut]
    cypher_context: str


class TraversalRequest(BaseModel):
    start_concept_id: str
    max_depth: int = 3
    direction: str = "both"  # "broader", "narrower", "both"


class ValidationReport(BaseModel):
    isolated_concepts: List[str]
    circular_hierarchies: List[List[str]]
    duplicate_labels: List[str]
    is_valid: bool
