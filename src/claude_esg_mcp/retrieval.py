"""Retrieval contract for ESG evidence search."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from claude_esg_mcp.config import RetrievalSettings
from claude_esg_mcp.embeddings import EmbeddingProvider


EXPECTED_EMBEDDING_DIMENSION = 1536
DEFAULT_STRATEGY = "vector"
SUPPORTED_STRATEGIES = frozenset({DEFAULT_STRATEGY})


class ChromaRetriever:
    """Thin adapter around a Chroma collection query interface."""

    def __init__(self, collection: Any) -> None:
        self.collection = collection

    @classmethod
    def from_settings(
        cls,
        settings: RetrievalSettings,
        client_factory: Any | None = None,
    ) -> "ChromaRetriever":
        """Create a retriever from the configured Chroma index path."""
        if client_factory is None:
            import chromadb

            client_factory = chromadb.PersistentClient

        client = client_factory(settings.index_path)
        collection = client.get_collection(settings.collection_name)
        return cls(collection=collection)

    def query(
        self,
        *,
        query_embedding: list[float],
        top_k: int,
        company: str | None,
    ) -> list[dict[str, Any]]:
        kwargs: dict[str, Any] = {
            "query_embeddings": [query_embedding],
            "n_results": top_k,
            "include": ["documents", "metadatas", "distances"],
        }
        if company:
            kwargs["where"] = {"company": company}

        response = self.collection.query(**kwargs)

        documents = response.get("documents", [[]])
        metadatas = response.get("metadatas", [[]])
        distances = response.get("distances", [[]])

        rows: list[dict[str, Any]] = []
        for document, metadata, distance in zip(
            documents[0] if documents else [],
            metadatas[0] if metadatas else [],
            distances[0] if distances else [],
        ):
            rows.append(
                {
                    "document": document,
                    "metadata": metadata,
                    "distance": distance,
                }
            )
        return rows


class RetrievalService:
    """Validation and formatting layer over vector retrieval."""

    def __init__(
        self,
        *,
        settings: RetrievalSettings,
        embedding_provider: EmbeddingProvider,
        retriever: Any,
        answer_generator: Any | None = None,
    ) -> None:
        self.settings = settings
        self.embedding_provider = embedding_provider
        self.retriever = retriever
        self.answer_generator = answer_generator

    def search_esg_reports(
        self,
        *,
        query: str,
        company: str | None = None,
        top_k: int | None = None,
        strategy: str | None = None,
    ) -> dict[str, Any]:
        normalized_query = query.strip()
        if not normalized_query:
            raise ValueError("query must be non-empty")

        strategy_value = strategy or DEFAULT_STRATEGY
        if strategy_value not in SUPPORTED_STRATEGIES:
            raise ValueError(
                f"strategy must be one of: {', '.join(sorted(SUPPORTED_STRATEGIES))}"
            )

        requested_top_k = self.settings.max_top_k if top_k is None else top_k
        if requested_top_k < 1:
            raise ValueError("top_k must be at least 1")
        bounded_top_k = min(requested_top_k, self.settings.max_top_k)

        query_embedding = self.embedding_provider.embed_query(
            normalized_query,
            self.settings.embedding_model,
        )
        if len(query_embedding) != EXPECTED_EMBEDDING_DIMENSION:
            raise ValueError(
                "query embedding dimension mismatch: expected 1536 dimensions"
            )

        raw_results = self.retriever.query(
            query_embedding=query_embedding,
            top_k=bounded_top_k,
            company=company,
        )

        return {
            "query": normalized_query,
            "strategy": strategy_value,
            "results": [
                self._format_result(result)
                for result in raw_results
            ],
        }

    def _format_result(self, result: Mapping[str, Any]) -> dict[str, Any]:
        metadata = dict(result.get("metadata", {}))
        company = str(metadata.get("company", ""))
        source_file = str(metadata.get("source_file", ""))
        page = metadata.get("page")
        chunk_id = str(metadata.get("chunk_id", ""))
        content = str(result.get("document", ""))[: self.settings.max_content_chars]
        distance = float(result.get("distance", 0.0))

        return {
            "company": company,
            "source_file": source_file,
            "page": page,
            "chunk_id": chunk_id,
            "content": content,
            "score": 1.0 / (1.0 + distance),
            "citation": f"{company} | {source_file} | p.{page} | {chunk_id}",
        }


def search_esg_reports(*args, **kwargs):
    """Compatibility wrapper kept for future integration."""
    raise NotImplementedError("Use RetrievalService.search_esg_reports instead")
