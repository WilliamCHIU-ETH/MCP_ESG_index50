# Claude ESG MCP Server

Local Claude-first MCP server for retrieving citation-ready evidence from the existing 50-company Taiwan ESG ChromaDB index.

## What It Does

- Exposes a single MCP tool: `search_esg_reports`
- Uses the existing `esg_reports_50` Chroma collection
- Generates query embeddings with OpenAI `text-embedding-3-small`
- Returns bounded evidence chunks with `company`, `source_file`, `page`, `chunk_id`, `content`, `score`, and `citation`
- Leaves final answer synthesis to Claude

## Project Metadata

- License: MIT
- Package metadata lives in `pyproject.toml`
- Repository: <https://github.com/WilliamCHIU-ETH/MCP_ESG_index50>

## Local Run

This project standardizes on Python 3.12, `uv`, and a local `.venv`.

Prerequisites:

- `uv`
- Python 3.12 available to `uv`

```bash
make setup
make run
```

Required environment variables:

- `OPENAI_API_KEY`
- `CLAUDE_ESG_INDEX_PATH`, pointing to a local ChromaDB index directory

Optional environment variables:

- `CLAUDE_ESG_COLLECTION_NAME` default: `esg_reports_50`
- `CLAUDE_ESG_EMBEDDING_MODEL` default: `text-embedding-3-small`
- `CLAUDE_ESG_MAX_TOP_K` default: `5`
- `CLAUDE_ESG_MAX_CONTENT_CHARS` default: `1200`

Copy `.env.example` to `.env` for local runtime values. The template is intentionally early-stage and may change as the project evolves. The ESG vector database is not included in this public repo.

## Developer Workflow

Install pre-commit hooks once per clone:

```bash
make pre-commit-install
```

Run formatting and lint checks:

```bash
make lint
make format
```

`pre-commit` runs `ruff format` and `ruff check` before each commit, so formatting and linting become part of the local commit path instead of a command you need to remember manually.

## Claude Desktop Config

Example Claude Desktop MCP config:

```json
{
  "mcpServers": {
    "claude-esg-mcp": {
      "command": "uv",
      "args": ["run", "claude-esg-mcp"],
      "cwd": "/absolute/path/to/MCP_ESG_index50",
      "env": {
        "OPENAI_API_KEY": "YOUR_OPENAI_API_KEY",
        "CLAUDE_ESG_INDEX_PATH": "/absolute/path/to/esg_50_vector_db",
        "CLAUDE_ESG_COLLECTION_NAME": "esg_reports_50",
        "CLAUDE_ESG_EMBEDDING_MODEL": "text-embedding-3-small",
        "CLAUDE_ESG_MAX_TOP_K": "5",
        "CLAUDE_ESG_MAX_CONTENT_CHARS": "1200"
      }
    }
  }
}
```

## Verification Commands

Run unit and contract tests. These tests must not call OpenAI, ChromaDB, or other real external services:

```bash
make test
```

Run integration tests. These may exercise multiple project components, but should still avoid real external services unless explicitly marked as smoke tests:

```bash
make integration
```

Run opt-in live smoke tests after configuring `.env`. Smoke tests may call OpenAI and the configured ESG ChromaDB index:

```bash
make smoke
```

Test layout:

```text
tests/
├── conftest.py          # Shared pytest import path setup and future fixtures
├── unit/                # Pure unit tests with fakes/mocks only
├── integration/         # Cross-component tests without live external services
└── smoke/               # Live API/index tests, skipped unless env is configured
```

Mocking rule: unit tests use fakes, `unittest.mock`, or `pytest-mock`; integration tests and above are the only layers allowed to touch broader runtime dependencies. Live external dependencies belong in `tests/smoke/`.

Verify the MCP tool is registered:

```bash
uv run python - <<'PY'
import asyncio
from claude_esg_mcp.server import build_mcp_server

class FakeRetrievalService:
    def search_esg_reports(self, **kwargs):
        return {"query": kwargs["query"], "strategy": "vector", "results": []}

async def main():
    server = build_mcp_server(retrieval_service=FakeRetrievalService())
    tools = await server.list_tools()
    print([tool.name for tool in tools])

asyncio.run(main())
PY
```
