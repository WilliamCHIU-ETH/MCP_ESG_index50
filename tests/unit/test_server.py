from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import pytest

from claude_esg_mcp.config import RetrievalSettings
from claude_esg_mcp.server import (
    build_default_retrieval_service,
    build_mcp_server,
    list_registered_tool_names,
    main,
)


@dataclass
class FakeRetrievalService:
    response: dict
    calls: list[dict] = field(default_factory=list)

    def search_esg_reports(
        self,
        *,
        query: str,
        company: str | None = None,
        top_k: int | None = None,
        strategy: str | None = None,
    ) -> dict:
        self.calls.append(
            {
                "query": query,
                "company": company,
                "top_k": top_k,
                "strategy": strategy,
            }
        )
        return self.response


class FakeFastMCP:
    def __init__(self, name: str) -> None:
        self.name = name
        self.registered_tools: list[Callable[..., object]] = []
        self.run_called = False

    def tool(self):
        def decorator(func):
            self.registered_tools.append(func)
            return func

        return decorator

    def run(self) -> None:
        self.run_called = True


class FakeCollection:
    def query(self, **kwargs) -> dict:
        return {"documents": [[]], "metadatas": [[]], "distances": [[]]}


def test_build_mcp_server_registers_search_tool_with_claude_focused_description() -> None:
    retrieval_service = FakeRetrievalService(response={"results": []})

    server = build_mcp_server(
        retrieval_service=retrieval_service,
        fastmcp_factory=FakeFastMCP,
    )

    assert server.name == "Claude ESG MCP"
    assert list_registered_tool_names(server) == ["search_esg_reports"]
    assert "Taiwan company ESG reports" in (server.registered_tools[0].__doc__ or "")
    assert "citation-ready evidence" in (server.registered_tools[0].__doc__ or "")


def test_registered_search_tool_calls_the_retrieval_service() -> None:
    retrieval_service = FakeRetrievalService(
        response={"query": "台積電", "strategy": "vector", "results": []}
    )
    server = build_mcp_server(
        retrieval_service=retrieval_service,
        fastmcp_factory=FakeFastMCP,
    )

    payload = server.registered_tools[0](
        query="台積電的碳中和目標是什麼",
        company="台積電",
        top_k=2,
        strategy="vector",
    )

    assert payload == {"query": "台積電", "strategy": "vector", "results": []}
    assert retrieval_service.calls == [
        {
            "query": "台積電的碳中和目標是什麼",
            "company": "台積電",
            "top_k": 2,
            "strategy": "vector",
        }
    ]


def test_build_default_retrieval_service_rejects_missing_index_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    missing_path = tmp_path / "missing-index"
    settings = RetrievalSettings(index_path=str(missing_path))
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    with pytest.raises(RuntimeError, match="index path"):
        build_default_retrieval_service(settings=settings)


def test_build_default_retrieval_service_rejects_missing_openai_api_key(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    index_path = tmp_path / "index"
    index_path.mkdir()
    settings = RetrievalSettings(index_path=str(index_path))
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        build_default_retrieval_service(settings=settings)


def test_build_default_retrieval_service_wraps_collection_load_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    index_path = tmp_path / "index"
    index_path.mkdir()
    settings = RetrievalSettings(index_path=str(index_path))
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    class BrokenClient:
        def get_collection(self, name: str) -> FakeCollection:
            raise ValueError("boom")

    with pytest.raises(RuntimeError, match="collection"):
        build_default_retrieval_service(
            settings=settings,
            client_factory=lambda path: BrokenClient(),
        )


def test_main_runs_the_mcp_server(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_server = FakeFastMCP("Claude ESG MCP")
    monkeypatch.setattr(
        "claude_esg_mcp.server.build_default_retrieval_service",
        lambda: object(),
    )
    monkeypatch.setattr(
        "claude_esg_mcp.server.build_mcp_server",
        lambda retrieval_service: fake_server,
    )

    main()

    assert fake_server.run_called is True
