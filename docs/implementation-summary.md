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

## Test Evidence

- `uv run pytest -q` -> `16 passed, 1 deselected`
- `make integration` -> `1 skipped, 16 deselected` when live env is not configured
- `make doctor` -> reports Python 3.12.4 and current environment variable state
- `openspec validate add-claude-esg-mcp-server --strict` -> valid
- Real FastMCP introspection via `await server.list_tools()` returns `['search_esg_reports']`
- Integration test path exists and copies the real local ChromaDB index to a writable temp directory before querying

## Known Limitations

- The live integration test is currently skipped because `OPENAI_API_KEY` is not set in this environment.
- Real-query validation for `台積電的碳中和目標是什麼` is not yet executed for the same reason.
- Manual Claude smoke tests are not yet run because this workspace does not currently have the required live Claude Desktop + API-key setup in place.
- Retrieval quality comparison between vector-only and alternate strategies is still pending live evaluation.

## Deferred Phase 2 Items

- Google embedding migration
- PostgreSQL + pgvector migration
- Hosted deployment
- Public API, UI, auth, and rate limiting
- User-uploaded PDFs and automatic corpus refresh
- Expanded retrieval evaluation beyond the MVP smoke/integration path
