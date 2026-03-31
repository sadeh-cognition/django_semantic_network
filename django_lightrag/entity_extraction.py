from loguru import logger
import os
import json
from dataclasses import dataclass
from typing import List, Tuple, Optional
from pydantic import BaseModel, Field
import litellm

class ExtractedConceptSchema(BaseModel):
    pref_label: str = Field(description="The preferred name of the concept")
    alt_labels: List[str] = Field(description="Synonyms or alternate names")
    definition: str = Field(description="A concise definition of the concept")
    broader_than: List[str] = Field(description="Preferred labels of broader/parent concepts")
    narrower_than: List[str] = Field(description="Preferred labels of narrower/child concepts")
    related_to: List[str] = Field(description="Preferred labels of related concepts")
    confidence: float = Field(description="Confidence score from 0.0 to 1.0")

class ExtractedGraphSchema(BaseModel):
    concepts: List[ExtractedConceptSchema] = Field(description="List of extracted SKOS concepts")
    relations: List[Tuple[str, str, str]] = Field(description="List of raw relationships (subject, predicate, object) where subject and object are concept preferred labels")

@dataclass
class ExtractedConcept:
    pref_label: str
    alt_labels: List[str]
    definition: str
    broader_than: List[str]
    narrower_than: List[str]
    related_to: List[str]
    confidence: float

@dataclass
class ExtractedGraph:
    concepts: List[ExtractedConcept]
    relations: List[Tuple[str, str, str]]

def extract_concepts_and_relations(text: str, model: str = None) -> ExtractedGraph:
    """
    Calls litellm to extract SKOS concepts and generic relations.
    """
    if model is None:
        model = os.environ.get("LLM_MODEL", "groq/llama-3.1-8b-instant")
        
    system_prompt = (
        "You are an expert knowledge graph extraction system. "
        "Extract key concepts and their relationships from the provided text following the SKOS (Simple Knowledge Organization System) model. "
        "For each concept, provide a pref_label, alt_labels (synonyms), a concise definition, "
        "and lists of broader_than, narrower_than, and related_to concepts (using their pref_labels). "
        "Also extract direct predicate relationships as (subject, predicate, object) tuples. "
        "Return the output as a valid JSON object matching the requested schema. "
    )

    try:
        # LiteLLM supports structured response with `response_format` 
        # But for llama-3 on groq, json_object is generally the way to go if standard Pydantic schema doesn't work.
        # Let's try passing the schema json explicitly.
        schema_prompt = f"JSON Schema:\n{ExtractedGraphSchema.model_json_schema()}"
        
        response = litellm.completion(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt + "\n" + schema_prompt},
                {"role": "user", "content": f"Extract knowledge from this text:\n\n{text}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.0
        )
        
        content = response.choices[0].message.content
        data = ExtractedGraphSchema.model_validate_json(content)
        
        ext_concepts = [
            ExtractedConcept(
                pref_label=c.pref_label,
                alt_labels=c.alt_labels,
                definition=c.definition,
                broader_than=c.broader_than,
                narrower_than=c.narrower_than,
                related_to=c.related_to,
                confidence=c.confidence
            ) for c in data.concepts
        ]
        
        return ExtractedGraph(
            concepts=ext_concepts,
            relations=data.relations
        )
        
    except Exception as e:
        logger.error(f"Error extracting graph using LLM: {e}")
        return ExtractedGraph(concepts=[], relations=[])
