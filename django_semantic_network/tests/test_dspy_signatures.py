from types import SimpleNamespace

import pytest

from django_semantic_network.entity_extraction import (
    ExtractedGraph,
    extract_concepts_and_relations,
)
from django_semantic_network.query_engine import _get_embedding, graphrag_query
from django_semantic_network.schemas import ConceptOut, SearchResult


@pytest.mark.django_db
def test_extract_concepts_uses_dspy_signature(monkeypatch):
    class FakeExtractor:
        def __call__(self, *, text):
            assert text == "The mitochondria is the powerhouse of the cell."
            return SimpleNamespace(
                extracted_graph=SimpleNamespace(
                    concepts=[
                        SimpleNamespace(
                            pref_label="mitochondria",
                            alt_labels=["mitochondrion"],
                            definition="Organelle that generates cellular energy.",
                            broader_than=["organelle"],
                            narrower_than=[],
                            related_to=["cell"],
                            confidence=0.99,
                        )
                    ],
                    relations=[("mitochondria", "part_of", "cell")],
                )
            )

    monkeypatch.setattr(
        "django_semantic_network.entity_extraction.get_default_chat_lm",
        lambda *_: object(),
    )
    monkeypatch.setattr(
        "django_semantic_network.entity_extraction.dspy.Predict",
        lambda *_: FakeExtractor(),
    )

    class FakeContext:
        def __enter__(self):
            return None

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(
        "django_semantic_network.entity_extraction.dspy.context",
        lambda **_: FakeContext(),
    )

    graph = extract_concepts_and_relations(
        "The mitochondria is the powerhouse of the cell."
    )

    assert isinstance(graph, ExtractedGraph)
    assert graph.concepts[0].pref_label == "mitochondria"
    assert graph.relations == [("mitochondria", "part_of", "cell")]


@pytest.mark.django_db
def test_graphrag_query_uses_dspy_signature(monkeypatch):
    monkeypatch.setattr(
        "django_semantic_network.query_engine.faceted_search",
        lambda query, filters, top_k: SearchResult(
            concepts=[
                ConceptOut(
                    id="c1",
                    pref_label="Relativity",
                    alt_labels=[],
                    definition="Theory developed by Einstein.",
                    confidence_score=1.0,
                )
            ],
            papers=[],
        ),
    )

    class FakeResult:
        def __init__(self):
            self._rows = iter(
                [["Relativity", "RELATED", "Einstein", "Theory developed by Einstein."]]
            )

        def has_next(self):
            if not hasattr(self, "_next"):
                try:
                    self._next = next(self._rows)
                except StopIteration:
                    self._next = None
            return self._next is not None

        def get_next(self):
            row = self._next
            self._next = None
            return row

    class FakeConn:
        def execute(self, query, params):
            assert params == {"ids": ["c1"]}
            return FakeResult()

    monkeypatch.setattr(
        "django_semantic_network.query_engine.get_ladybug_connection",
        lambda: FakeConn(),
    )
    monkeypatch.setattr(
        "django_semantic_network.query_engine.get_default_chat_lm", lambda *_: object()
    )

    class FakeGenerator:
        def __call__(self, *, question, graph_context):
            assert "Relativity" in graph_context
            return "Einstein developed relativity."

    monkeypatch.setattr(
        "django_semantic_network.query_engine.GroundedAnswerGenerator",
        lambda: FakeGenerator(),
    )

    class FakeContext:
        def __enter__(self):
            return None

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(
        "django_semantic_network.query_engine.dspy.context", lambda **_: FakeContext()
    )

    response = graphrag_query("What theory did Einstein develop?", top_k=1)

    assert response.answer == "Einstein developed relativity."
    assert response.grounding_concepts[0].id == "c1"


def test_get_embedding_uses_embed_gen(monkeypatch):
    monkeypatch.setattr(
        "django_semantic_network.query_engine.get_embedding_config",
        lambda: ("test-model", "LMStudio", "http://embed-host"),
    )
    monkeypatch.setattr(
        "django_semantic_network.query_engine.generate_embeddings",
        lambda texts, model_name, provider, base_url: (
            texts == ["query text"]
            and model_name == "test-model"
            and provider == "LMStudio"
            and base_url == "http://embed-host"
            and [[0.1, 0.2, 0.3]]
        ),
    )

    assert _get_embedding("query text") == [0.1, 0.2, 0.3]
