from typing import List, Tuple

from pydantic import BaseModel, Field


class ExtractedConceptSchema(BaseModel):
    pref_label: str = Field(description="The preferred name of the concept")
    alt_labels: List[str] = Field(description="Synonyms or alternate names")
    definition: str = Field(description="A concise definition of the concept")
    broader_than: List[str] = Field(
        description="Preferred labels of broader or parent concepts"
    )
    narrower_than: List[str] = Field(
        description="Preferred labels of narrower or child concepts"
    )
    related_to: List[str] = Field(description="Preferred labels of related concepts")
    confidence: float = Field(description="Confidence score from 0.0 to 1.0")


class ExtractedGraph(BaseModel):
    concepts: List[ExtractedConceptSchema] = Field(
        description="List of extracted SKOS concepts"
    )
    relations: List[Tuple[str, str, str]] = Field(
        description=(
            "List of raw relationships as (subject, predicate, object) tuples where "
            "subject and object are concept preferred labels"
        )
    )
