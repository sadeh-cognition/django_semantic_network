import pytest
from django_lightrag.schemas import IngestRequest, SearchRequest, GraphRAGRequest, TraversalRequest

@pytest.mark.django_db
def test_ingest_endpoint(ninja_client):
    payload = IngestRequest(
        text="Einstein developed the theory of relativity.", 
        source_id="test-val-1"
    )
    # Testing functional ingestion using real external LLMs and databases as specified
    response = ninja_client.post("/ingest", json=payload.model_dump())
    assert response.status_code == 200
    data = response.json()
    assert "concepts_extracted" in data
    assert data["status"] == "success"

@pytest.mark.django_db
def test_search_endpoint(ninja_client):
    payload = SearchRequest(query="theory", top_k=2)
    response = ninja_client.post("/search", json=payload.model_dump())
    assert response.status_code == 200
    data = response.json()
    assert "concepts" in data
    # Might be empty if ingestion above didn't extract 'theory' but schema ensures the key exists.
    assert isinstance(data["concepts"], list)

@pytest.mark.django_db
def test_graphrag_endpoint(ninja_client):
    payload = GraphRAGRequest(natural_language_query="What theory did Einstein develop?", top_k=2)
    response = ninja_client.post("/graphrag", json=payload.model_dump())
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "grounding_concepts" in data

@pytest.mark.django_db
def test_validate_endpoint(ninja_client):
    response = ninja_client.get("/validate")
    assert response.status_code == 200
    data = response.json()
    assert "is_valid" in data
