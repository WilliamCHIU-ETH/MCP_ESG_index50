"""Retrieval contract for ESG evidence search."""

from __future__ import annotations

from collections.abc import Mapping
import json
from pathlib import Path
import pickle
import sqlite3
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
        migrate_legacy_chroma_config(settings.index_path)
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
            raise ValueError(f"strategy must be one of: {', '.join(sorted(SUPPORTED_STRATEGIES))}")

        requested_top_k = self.settings.max_top_k if top_k is None else top_k
        if requested_top_k < 1:
            raise ValueError("top_k must be at least 1")
        bounded_top_k = min(requested_top_k, self.settings.max_top_k)

        query_embedding = self.embedding_provider.embed_query(
            normalized_query,
            self.settings.embedding_model,
        )
        if len(query_embedding) != EXPECTED_EMBEDDING_DIMENSION:
            raise ValueError("query embedding dimension mismatch: expected 1536 dimensions")

        raw_results = self.retriever.query(
            query_embedding=query_embedding,
            top_k=bounded_top_k,
            company=company,
        )

        return {
            "query": normalized_query,
            "strategy": strategy_value,
            "results": [self._format_result(result) for result in raw_results],
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


def migrate_legacy_chroma_config(index_path: str) -> None:
    """Migrate legacy Chroma collection config JSON to the 0.6.x shape."""
    sqlite_path = Path(index_path) / "chroma.sqlite3"
    if not sqlite_path.exists():
        return

    connection = sqlite3.connect(sqlite_path)
    try:
        rows = connection.execute(
            "SELECT id, config_json_str FROM collections WHERE config_json_str IS NOT NULL"
        ).fetchall()
        updates: list[tuple[str, str]] = []
        for collection_id, raw_config in rows:
            try:
                config = json.loads(raw_config)
            except json.JSONDecodeError:
                continue

            if config.get("_type") == "CollectionConfigurationInternal":
                continue

            hnsw = config.get("vector_index", {}).get("hnsw")
            if not isinstance(hnsw, dict):
                continue

            migrated = {
                "hnsw_configuration": {
                    "space": hnsw.get("space", "l2"),
                    "ef_construction": hnsw.get("ef_construction", 100),
                    "ef_search": hnsw.get("ef_search", 100),
                    "num_threads": hnsw.get("num_threads", 8),
                    "M": hnsw.get("M", hnsw.get("max_neighbors", 16)),
                    "resize_factor": hnsw.get("resize_factor", 1.2),
                    "batch_size": hnsw.get("batch_size", 100),
                    "sync_threshold": hnsw.get("sync_threshold", 1000),
                    "_type": "HNSWConfigurationInternal",
                },
                "_type": "CollectionConfigurationInternal",
            }
            updates.append((json.dumps(migrated), collection_id))

        if updates:
            connection.executemany(
                "UPDATE collections SET config_json_str = ? WHERE id = ?",
                updates,
            )
            connection.commit()
        migrate_legacy_hnsw_pickles(Path(index_path), connection)
    finally:
        connection.close()


def migrate_legacy_hnsw_pickles(index_path: Path, connection: sqlite3.Connection) -> None:
    """Rewrite legacy HNSW pickle payloads into PersistentData objects."""
    try:
        rows = connection.execute(
            """
            SELECT segments.id, collections.dimension
            FROM segments
            JOIN collections ON collections.id = segments.collection
            WHERE segments.scope = 'VECTOR'
            """
        ).fetchall()
    except sqlite3.OperationalError:
        return

    if not rows:
        return

    from chromadb.segment.impl.vector.local_persistent_hnsw import PersistentData

    for segment_id, dimension in rows:
        metadata_path = index_path / str(segment_id) / "index_metadata.pickle"
        if not metadata_path.exists():
            continue

        with metadata_path.open("rb") as handle:
            payload = pickle.load(handle)

        if isinstance(payload, PersistentData):
            if payload.dimensionality is None and dimension is not None:
                payload.dimensionality = int(dimension)
                with metadata_path.open("wb") as handle:
                    pickle.dump(payload, handle)
            continue

        if not isinstance(payload, dict):
            continue

        migrated = PersistentData(
            dimensionality=int(dimension)
            if dimension is not None
            else payload.get("dimensionality"),
            total_elements_added=int(payload.get("total_elements_added", 0)),
            id_to_label=dict(payload.get("id_to_label", {})),
            label_to_id=dict(payload.get("label_to_id", {})),
            id_to_seq_id=dict(payload.get("id_to_seq_id", {})),
        )
        with metadata_path.open("wb") as handle:
            pickle.dump(migrated, handle)
