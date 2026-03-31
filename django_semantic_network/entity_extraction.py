import os
from dataclasses import dataclass
from typing import List, Tuple

import dspy
from loguru import logger

from .dspy_runtime import get_default_chat_lm
from .llm_signatures import ExtractConceptGraphSignature


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
    Calls DSPy to extract SKOS concepts and generic relations.
    """
    try:
        lm = get_default_chat_lm(model or os.environ.get("LLM_MODEL"))
        extractor = dspy.Predict(ExtractConceptGraphSignature)
        with dspy.context(lm=lm):
            data = extractor(text=text)

        ext_concepts = [
            ExtractedConcept(
                pref_label=c.pref_label,
                alt_labels=c.alt_labels,
                definition=c.definition,
                broader_than=c.broader_than,
                narrower_than=c.narrower_than,
                related_to=c.related_to,
                confidence=c.confidence,
            )
            for c in data.extracted_graph.concepts
        ]

        return ExtractedGraph(
            concepts=ext_concepts, relations=data.extracted_graph.relations
        )

    except Exception as e:
        logger.error(f"Error extracting graph using LLM: {e}")
        return ExtractedGraph(concepts=[], relations=[])
