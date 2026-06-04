from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pytest

from claude_esg_mcp.config import RetrievalSettings
from claude_esg_mcp.server import build_default_retrieval_service


pytestmark = pytest.mark.integration


@dataclass
class FakeEmbeddingProvider:
    vector: list[float]
    calls: list[tuple[str, str]] = field(default_factory=list)

    def embed_query(self, query: str, model: str) -> list[float]:
        self.calls.append((query, model))
        return self.vector


class FakeCollection:
    def __init__(self) -> None:
        self.query_calls: list[dict] = []

    def query(self, **kwargs) -> dict:
        self.query_calls.append(kwargs)
        return {
            "documents": [["台積電承諾 2050 淨零排放"]],
            "metadatas": [
                [
                    {
                        "company": "台積電",
                        "source_file": "tsmc_esg_2023.pdf",
                        "page": 42,
                        "chunk_id": "chunk-042",
                    }
                ]
            ],
            "distances": [[0.1]],
        }


class FakeClient:
    def __init__(self, collection: FakeCollection) -> None:
        self.collection = collection
        self.requested_paths: list[str] = []
        self.requested_collections: list[str] = []

    def get_collection(self, name: str) -> FakeCollection:
        self.requested_collections.append(name)
        return self.collection


def test_default_service_wires_settings_embedding_provider_and_chroma_adapter(
    tmp_path: Path,
) -> None:
    index_path = tmp_path / "index"
    index_path.mkdir()
    settings = RetrievalSettings(
        index_path=str(index_path),
        collection_name="esg_reports_50",
        embedding_model="text-embedding-3-small",
        max_top_k=2,
        max_content_chars=20,
    )
    embedding_provider = FakeEmbeddingProvider(vector=[0.01] * 1536)
    collection = FakeCollection()
    client = FakeClient(collection)

    service = build_default_retrieval_service(
        settings=settings,
        client_factory=lambda path: client,
        embedding_provider=embedding_provider,
    )

    payload = service.search_esg_reports(
        query="台積電碳中和",
        company="台積電",
        top_k=2,
    )

    assert embedding_provider.calls == [("台積電碳中和", "text-embedding-3-small")]
    assert client.requested_collections == ["esg_reports_50"]
    assert collection.query_calls[0]["where"] == {"company": "台積電"}
    assert len(collection.query_calls[0]["query_embeddings"][0]) == 1536
    assert payload["results"][0]["citation"] == "台積電 | tsmc_esg_2023.pdf | p.42 | chunk-042"
