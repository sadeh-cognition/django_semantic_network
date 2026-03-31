import httpx
from django_semantic_network.schemas import (
    IngestRequest,
    IngestResponse,
    SearchRequest,
    SearchResult,
    GraphRAGRequest,
    GraphRAGResponse,
    TraversalRequest,
    ValidationReport,
)


class KGClient:
    def __init__(self, base_url="http://localhost:8001/api"):
        self.base_url = base_url
        self.client = httpx.Client(timeout=60.0)

    def ingest(self, req: IngestRequest) -> IngestResponse:
        res = self.client.post(
            f"{self.base_url}/ingest", json=req.model_dump(exclude_none=True)
        )
        res.raise_for_status()
        return IngestResponse(**res.json())

    def search(self, req: SearchRequest) -> SearchResult:
        res = self.client.post(
            f"{self.base_url}/search", json=req.model_dump(exclude_none=True)
        )
        res.raise_for_status()
        return SearchResult(**res.json())

    def graphrag(self, req: GraphRAGRequest) -> GraphRAGResponse:
        res = self.client.post(
            f"{self.base_url}/graphrag", json=req.model_dump(exclude_none=True)
        )
        res.raise_for_status()
        return GraphRAGResponse(**res.json())

    def traverse(self, req: TraversalRequest) -> list:
        res = self.client.post(
            f"{self.base_url}/graph/traverse", json=req.model_dump(exclude_none=True)
        )
        res.raise_for_status()
        return res.json()

    def validate(self) -> ValidationReport:
        res = self.client.get(f"{self.base_url}/validate")
        res.raise_for_status()
        return ValidationReport(**res.json())
