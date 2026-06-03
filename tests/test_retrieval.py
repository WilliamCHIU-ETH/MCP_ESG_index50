from dataclasses import dataclass, field

import pytest

from claude_esg_mcp.config import RetrievalSettings
from claude_esg_mcp.retrieval import ChromaRetriever, RetrievalService


def make_embedding_vector(size: int) -> list[float]:
    return [0.01] * size


@dataclass
class FakeEmbeddingProvider:
    vector: list[float]
    calls: list[tuple[str, str]] = field(default_factory=list)

    def embed_query(self, query: str, model: str) -> list[float]:
        self.calls.append((query, model))
        return self.vector


@dataclass
class FakeRetriever:
    raw_results: list[dict]
    calls: list[dict] = field(default_factory=list)

    def query(self, *, query_embedding: list[float], top_k: int, company: str | None):
        self.calls.append(
            {
                "query_embedding": query_embedding,
                "top_k": top_k,
                "company": company,
            }
        )
        return self.raw_results


@dataclass
class FakeAnswerGenerator:
    calls: list[dict] = field(default_factory=list)

    def generate(self, *, query: str, results: list[dict]) -> str:
        self.calls.append({"query": query, "results": results})
        return "這不該被呼叫"


class FakeCollection:
    def __init__(self, response: dict | None = None) -> None:
        self.response = response or {
            "documents": [["段落內容"]],
            "metadatas": [[{"company": "台積電", "source_file": "tsmc.pdf", "page": 12, "chunk_id": "chunk-001"}]],
            "distances": [[0.25]],
        }
        self.query_calls: list[dict] = []

    def query(self, **kwargs) -> dict:
        self.query_calls.append(kwargs)
        return self.response


class FakeClient:
    def __init__(self, collection: FakeCollection) -> None:
        self.collection = collection
        self.requested_names: list[str] = []

    def get_collection(self, name: str) -> FakeCollection:
        self.requested_names.append(name)
        return self.collection


@pytest.fixture
def settings() -> RetrievalSettings:
    return RetrievalSettings(
        index_path="/tmp/esg_50_vector_db",
        collection_name="esg_reports_50",
        embedding_model="text-embedding-3-small",
        max_top_k=3,
        max_content_chars=11,
    )


def test_search_rejects_blank_query(settings: RetrievalSettings) -> None:
    service = RetrievalService(
        settings=settings,
        embedding_provider=FakeEmbeddingProvider(make_embedding_vector(1536)),
        retriever=FakeRetriever(raw_results=[]),
    )

    with pytest.raises(ValueError, match="query"):
        service.search_esg_reports(query="   ")


def test_search_rejects_unsupported_strategy(settings: RetrievalSettings) -> None:
    service = RetrievalService(
        settings=settings,
        embedding_provider=FakeEmbeddingProvider(make_embedding_vector(1536)),
        retriever=FakeRetriever(raw_results=[]),
    )

    with pytest.raises(ValueError, match="strategy"):
        service.search_esg_reports(query="台積電碳中和", strategy="hybrid")


def test_search_caps_top_k_at_configured_maximum(settings: RetrievalSettings) -> None:
    retriever = FakeRetriever(raw_results=[])
    service = RetrievalService(
        settings=settings,
        embedding_provider=FakeEmbeddingProvider(make_embedding_vector(1536)),
        retriever=retriever,
    )

    service.search_esg_reports(query="台積電碳中和", top_k=99)

    assert retriever.calls[0]["top_k"] == settings.max_top_k


def test_search_rejects_non_1536_query_embeddings_before_retrieval(
    settings: RetrievalSettings,
) -> None:
    retriever = FakeRetriever(raw_results=[])
    service = RetrievalService(
        settings=settings,
        embedding_provider=FakeEmbeddingProvider(make_embedding_vector(384)),
        retriever=retriever,
    )

    with pytest.raises(ValueError, match="1536"):
        service.search_esg_reports(query="台積電碳中和")

    assert retriever.calls == []


def test_search_uses_1536_query_embeddings(settings: RetrievalSettings) -> None:
    embedding_provider = FakeEmbeddingProvider(make_embedding_vector(1536))
    retriever = FakeRetriever(raw_results=[])
    service = RetrievalService(
        settings=settings,
        embedding_provider=embedding_provider,
        retriever=retriever,
    )

    service.search_esg_reports(query="台積電碳中和", company="台積電")

    assert embedding_provider.calls == [("台積電碳中和", settings.embedding_model)]
    assert len(retriever.calls[0]["query_embedding"]) == 1536
    assert retriever.calls[0]["company"] == "台積電"


def test_chroma_retriever_queries_with_embeddings_and_company_filter() -> None:
    query_embedding = make_embedding_vector(1536)
    collection = FakeCollection()
    retriever = ChromaRetriever(collection=collection)

    retriever.query(query_embedding=query_embedding, top_k=2, company="台積電")

    assert collection.query_calls == [
        {
            "query_embeddings": [query_embedding],
            "n_results": 2,
            "where": {"company": "台積電"},
            "include": ["documents", "metadatas", "distances"],
        }
    ]


def test_chroma_retriever_loads_the_configured_collection(
    settings: RetrievalSettings,
) -> None:
    collection = FakeCollection()
    created_paths: list[str] = []
    client = FakeClient(collection)

    def fake_client_factory(path: str) -> FakeClient:
        created_paths.append(path)
        return client

    retriever = ChromaRetriever.from_settings(
        settings,
        client_factory=fake_client_factory,
    )

    assert created_paths == [settings.index_path]
    assert client.requested_names == [settings.collection_name]
    assert retriever.collection is collection


def test_chroma_retriever_omits_company_filter_when_not_provided() -> None:
    collection = FakeCollection()
    retriever = ChromaRetriever(collection=collection)

    retriever.query(query_embedding=make_embedding_vector(1536), top_k=2, company=None)

    assert "where" not in collection.query_calls[0]


def test_search_returns_citation_ready_bounded_evidence(settings: RetrievalSettings) -> None:
    raw_results = [
        {
            "document": "這是一段非常長的台積電永續報告內容",
            "metadata": {
                "company": "台積電",
                "source_file": "tsmc_esg_2023.pdf",
                "page": 88,
                "chunk_id": "chunk-123",
            },
            "distance": 0.25,
        }
    ]
    service = RetrievalService(
        settings=settings,
        embedding_provider=FakeEmbeddingProvider(make_embedding_vector(1536)),
        retriever=FakeRetriever(raw_results=raw_results),
    )

    payload = service.search_esg_reports(query="台積電碳中和")

    assert payload["strategy"] == "vector"
    assert payload["results"] == [
        {
            "company": "台積電",
            "source_file": "tsmc_esg_2023.pdf",
            "page": 88,
            "chunk_id": "chunk-123",
            "content": "這是一段非常長的台積電",
            "score": pytest.approx(0.8),
            "citation": "台積電 | tsmc_esg_2023.pdf | p.88 | chunk-123",
        }
    ]


def test_search_returns_evidence_only_without_backend_answer_generation(
    settings: RetrievalSettings,
) -> None:
    answer_generator = FakeAnswerGenerator()
    service = RetrievalService(
        settings=settings,
        embedding_provider=FakeEmbeddingProvider(make_embedding_vector(1536)),
        retriever=FakeRetriever(
            raw_results=[
                {
                    "document": "台積電承諾 2050 淨零",
                    "metadata": {
                        "company": "台積電",
                        "source_file": "tsmc_esg_2023.pdf",
                        "page": 42,
                        "chunk_id": "chunk-042",
                    },
                    "distance": 0.1,
                }
            ]
        ),
        answer_generator=answer_generator,
    )

    payload = service.search_esg_reports(query="台積電的碳中和目標是什麼")

    assert "answer" not in payload
    assert payload["results"][0]["citation"] == "台積電 | tsmc_esg_2023.pdf | p.42 | chunk-042"
    assert answer_generator.calls == []
