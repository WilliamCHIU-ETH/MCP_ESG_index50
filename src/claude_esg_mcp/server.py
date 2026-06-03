"""MCP server entrypoint."""

from __future__ import annotations

import os
from pathlib import Path
import sys
from typing import Any, Callable

from claude_esg_mcp.config import RetrievalSettings
from claude_esg_mcp.embeddings import OpenAIEmbeddingProvider
from claude_esg_mcp.retrieval import ChromaRetriever, RetrievalService


SERVER_NAME = "Claude ESG MCP"
TOOL_NAME = "search_esg_reports"
TOOL_DESCRIPTION = (
    "Search Taiwan company ESG reports and return citation-ready evidence "
    "chunks for Claude to cite in the final answer."
)


def _ensure_vendor_path() -> None:
    """Allow local .vendor installs to satisfy runtime imports."""
    vendor_path = Path(__file__).resolve().parents[2] / ".vendor"
    if vendor_path.exists():
        vendor_str = str(vendor_path)
        if vendor_str not in sys.path:
            sys.path.insert(0, vendor_str)


def build_default_retrieval_service(
    *,
    settings: RetrievalSettings | None = None,
    client_factory: Callable[[str], Any] | None = None,
    embedding_provider: Any | None = None,
) -> RetrievalService:
    """Construct the default retrieval service used by the MCP server."""
    resolved_settings = settings or RetrievalSettings.from_env()
    index_path = Path(resolved_settings.index_path)
    if not index_path.exists():
        raise RuntimeError(f"Missing configured index path: {resolved_settings.index_path}")

    if embedding_provider is None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is required to start the MCP server")
        embedding_provider = OpenAIEmbeddingProvider(api_key=api_key)

    try:
        retriever = ChromaRetriever.from_settings(
            resolved_settings,
            client_factory=client_factory,
        )
    except Exception as exc:
        raise RuntimeError(
            "Failed to load collection "
            f"'{resolved_settings.collection_name}' from '{resolved_settings.index_path}'"
        ) from exc

    return RetrievalService(
        settings=resolved_settings,
        embedding_provider=embedding_provider,
        retriever=retriever,
    )


def build_mcp_server(
    *,
    retrieval_service: RetrievalService | Any,
    fastmcp_factory: Callable[[str], Any] | None = None,
) -> Any:
    """Build the FastMCP server and register the ESG search tool."""
    if fastmcp_factory is None:
        _ensure_vendor_path()
        try:
            from mcp.server.fastmcp import FastMCP
        except ImportError as exc:
            raise RuntimeError(
                "The 'mcp' package is required to build the stdio MCP server"
            ) from exc
        fastmcp_factory = FastMCP

    mcp_server = fastmcp_factory(SERVER_NAME)

    @mcp_server.tool()
    def search_esg_reports(
        query: str,
        company: str | None = None,
        top_k: int | None = None,
        strategy: str | None = None,
    ) -> dict[str, Any]:
        """Search Taiwan company ESG reports and return citation-ready evidence for Claude."""
        return retrieval_service.search_esg_reports(
            query=query,
            company=company,
            top_k=top_k,
            strategy=strategy,
        )

    return mcp_server


def list_registered_tool_names(server: Any) -> list[str]:
    """Return registered tool names for test-time verification."""
    if hasattr(server, "registered_tools"):
        return [tool.__name__ for tool in server.registered_tools]
    return []


def main() -> None:
    """Run the stdio MCP server."""
    retrieval_service = build_default_retrieval_service()
    mcp_server = build_mcp_server(retrieval_service=retrieval_service)
    mcp_server.run()


if __name__ == "__main__":
    main()
