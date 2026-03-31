from types import SimpleNamespace

from django_semantic_network.entity_extraction import extract_concepts_and_relations


def test_extract_concepts(monkeypatch):
    class FakeExtractor:
        def __call__(self, *, text):
            assert text == "The mitochondria is the powerhouse of the cell."
            return SimpleNamespace(concepts=[], relations=[])

    class FakeContext:
        def __enter__(self):
            return None

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(
        "django_semantic_network.entity_extraction.get_default_chat_lm",
        lambda *_: object(),
    )
    monkeypatch.setattr(
        "django_semantic_network.entity_extraction.ConceptGraphExtractor",
        lambda: FakeExtractor(),
    )
    monkeypatch.setattr(
        "django_semantic_network.entity_extraction.dspy.context",
        lambda **_: FakeContext(),
    )

    graph = extract_concepts_and_relations(
        "The mitochondria is the powerhouse of the cell."
    )
    assert isinstance(graph.concepts, list)
    assert isinstance(graph.relations, list)
