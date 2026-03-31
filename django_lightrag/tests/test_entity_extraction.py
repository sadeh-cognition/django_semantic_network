import pytest
from django_lightrag.entity_extraction import extract_concepts_and_relations

def test_extract_concepts():
    text = "The mitochondria is the powerhouse of the cell."
    graph = extract_concepts_and_relations(text) # Uses groq automatically
    assert isinstance(graph.concepts, list)
    assert isinstance(graph.relations, list)
