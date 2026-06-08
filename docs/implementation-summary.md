# Implementation Summary

## Implemented Behavior

- Added a minimal Python package for the Claude ESG MCP server.
- Implemented `RetrievalSettings` with configurable index path, collection name, embedding model, maximum `top_k`, and maximum content length.
- Implemented an embedding provider interface plus an OpenAI-backed query embedding provider for `text-embedding-3-small`.
- Implemented a Chroma retrieval adapter that loads `esg_reports_50`, queries with `query_embeddings`, and supports optional company filtering.
- Implemented vector-only search as the default retrieval strategy.
- Implemented citation-ready result formatting with bounded content and stable citation strings.
- Implemented a FastMCP stdio server that exposes `search_esg_reports` and connects directly to the tested retrieval core.
- Standardized the project workflow on Python 3.12, `uv`, `.venv`, and `uv.lock`.
- Kept local `.vendor` runtime support as a legacy fallback, but the documented workflow now uses `uv run`.
- Added MIT licensing, complete public package metadata, and local pre-commit hooks for Ruff formatting/checking.
- Split tests into `unit`, `integration`, and `smoke` directories with live dependencies isolated to smoke tests.
- Added on-load migration for legacy ChromaDB collection config and HNSW pickle metadata so the existing ESG index remains queryable under the current runtime.

## Test Evidence

- `uv run pytest -q` -> `18 passed, 2 deselected`
- `uv run pytest -q -m smoke -k real_query` -> `1 passed, 19 deselected` against a temp copy of the real ESG index after configuring `OPENAI_API_KEY`
- `make integration` -> `1 skipped, 16 deselected` when live env is not configured
- `make doctor` -> reports Python 3.12.4 and current environment variable state
- `openspec validate add-claude-esg-mcp-server --strict` -> valid
- Real FastMCP introspection via `await server.list_tools()` returns `['search_esg_reports']`
- Integration test path exists and copies the real local ChromaDB index to a writable temp directory before querying
- Claude Desktop feasibility smoke test completed on 2026-06-08 with 6 manual queries covering connection smoke plus factual, quantitative, and explanatory retrieval. All 6 queries returned cited answers with `source_file` and `page` metadata, confirming the local Claude Desktop to MCP stdio path is workable for feasibility validation.

## Known Limitations

- The 2026-06-08 Claude Desktop smoke run establishes feasibility, not full retrieval validation. The broader 20-30 question manual pass and explicit failure taxonomy are deferred to follow-up validation work.
- Retrieval quality comparison between vector-only and alternate strategies is still pending follow-up evaluation.

## Deferred Phase 2 Items

- Google embedding migration
- PostgreSQL + pgvector migration
- Hosted deployment
- Public API, UI, auth, and rate limiting
- User-uploaded PDFs and automatic corpus refresh
- Expanded retrieval evaluation beyond the MVP smoke/integration path
