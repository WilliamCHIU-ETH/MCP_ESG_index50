"""Configuration models for the Claude ESG MCP server."""

from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(slots=True)
class RetrievalSettings:
    """Runtime settings for the retrieval core."""

    index_path: str
    collection_name: str = "esg_reports_50"
    embedding_model: str = "text-embedding-3-small"
    max_top_k: int = 5
    max_content_chars: int = 1200

    def __post_init__(self) -> None:
        if not self.index_path.strip():
            raise ValueError("index_path is required; set CLAUDE_ESG_INDEX_PATH")
        if self.max_top_k < 1:
            raise ValueError("max_top_k must be at least 1")
        if self.max_content_chars < 1:
            raise ValueError("max_content_chars must be at least 1")

    @classmethod
    def from_env(cls) -> "RetrievalSettings":
        """Build settings from environment variables."""
        return cls(
            index_path=os.environ.get("CLAUDE_ESG_INDEX_PATH", ""),
            collection_name=os.environ.get(
                "CLAUDE_ESG_COLLECTION_NAME",
                "esg_reports_50",
            ),
            embedding_model=os.environ.get(
                "CLAUDE_ESG_EMBEDDING_MODEL",
                "text-embedding-3-small",
            ),
            max_top_k=int(os.environ.get("CLAUDE_ESG_MAX_TOP_K", "5")),
            max_content_chars=int(
                os.environ.get("CLAUDE_ESG_MAX_CONTENT_CHARS", "1200")
            ),
        )
