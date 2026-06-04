# Add Claude ESG MCP Server Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task by task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Claude-first local stdio MCP server that exposes `search_esg_reports` against the existing 50-company ChromaDB index and returns citation-ready evidence chunks without backend answer generation.

**Architecture:** Create a minimal Python package in this repo with three layers: configuration, retrieval core, and MCP server entrypoint. Keep retrieval pure and testable with fake embedding/collection adapters, and reserve real ChromaDB/index access for opt-in integration tests that use a temporary writable copy of the local database.

**Tech Stack:** Python 3.12, uv, pytest, pydantic-settings, OpenAI embeddings API, ChromaDB, MCP Python SDK

---

## File Map

- Create: `pyproject.toml`
- Create: `src/claude_esg_mcp/__init__.py`
- Create: `src/claude_esg_mcp/config.py`
- Create: `src/claude_esg_mcp/models.py`
- Create: `src/claude_esg_mcp/embeddings.py`
- Create: `src/claude_esg_mcp/retrieval.py`
- Create: `src/claude_esg_mcp/server.py`
- Create: `tests/conftest.py`
- Create: `tests/unit/test_retrieval.py`
- Create: `tests/unit/test_server.py`
- Create: `tests/smoke/test_live_retrieval.py`
- Modify: `openspec/changes/add-claude-esg-mcp-server/tasks.md`

### Task 1: Scaffold the minimal Python project

**Files:**
- Create: `pyproject.toml`
- Create: `src/claude_esg_mcp/__init__.py`
- Create: `tests/conftest.py`

- [ ] Add package metadata, runtime dependencies, pytest configuration, and a source-layout package.
- [ ] Add shared fake objects/fixtures for embedding providers and Chroma collections.
- [ ] Run `pytest -q` and confirm collection fails because retrieval/server tests do not exist yet or import stubs are missing.

### Task 2: Lock the retrieval contract with failing tests

**Files:**
- Create: `tests/unit/test_retrieval.py`
- Create: `src/claude_esg_mcp/models.py`
- Create: `src/claude_esg_mcp/retrieval.py`

- [ ] Write a failing test for non-empty `query`, supported `strategy`, and bounded `top_k`.
- [ ] Run `pytest tests/unit/test_retrieval.py -q` and verify failure is caused by missing retrieval contract implementation.
- [ ] Write a failing test proving the embedding provider must return exactly 1536 dimensions before any Chroma query runs.
- [ ] Run `pytest tests/unit/test_retrieval.py -q` and verify the dimension test fails for the expected reason.
- [ ] Write a failing test proving Chroma is called with `query_embeddings` plus optional `where={"company": ...}` filtering.
- [ ] Write a failing test proving each formatted result includes `company`, `source_file`, `page`, `chunk_id`, `content`, `score`, and `citation`, and that the returned payload is evidence chunks rather than a generated final answer.

### Task 3: Implement the retrieval core

**Files:**
- Create: `src/claude_esg_mcp/config.py`
- Create: `src/claude_esg_mcp/embeddings.py`
- Create: `src/claude_esg_mcp/retrieval.py`

- [ ] Implement settings for index path, collection name, embedding model, maximum `top_k`, and content-length bound.
- [ ] Implement an embedding provider protocol and an OpenAI `text-embedding-3-small` provider.
- [ ] Implement a Chroma adapter that opens `esg_reports_50`, queries via `query_embeddings`, and supports optional company filtering.
- [ ] Implement vector-only search as the default and reject unsupported strategies before retrieval.
- [ ] Implement citation-ready formatting with bounded content and stable citation strings.
- [ ] Run `pytest tests/unit/test_retrieval.py -q` until all retrieval tests pass.

### Task 4: Expose the MCP server

**Files:**
- Create: `src/claude_esg_mcp/server.py`
- Create: `tests/unit/test_server.py`

- [ ] Add the MCP Python SDK dependency and a stdio server entrypoint.
- [ ] Register `search_esg_reports` with a Claude-oriented description and input schema.
- [ ] Connect the tool handler to the tested retrieval core.
- [ ] Add startup/configuration error handling for missing index path, missing API key, and collection-load failure.
- [ ] Add a test or command-level verification that the server advertises `search_esg_reports`.
- [ ] Run `pytest tests/unit/test_server.py -q` until the server contract passes.

### Task 5: Add integration verification and close the change

**Files:**
- Create: `tests/smoke/test_live_retrieval.py`
- Modify: `openspec/changes/add-claude-esg-mcp-server/tasks.md`

- [ ] Add an opt-in integration test path that copies the `CLAUDE_ESG_INDEX_PATH` ChromaDB index into a writable temp directory before loading Chroma.
- [ ] Add a real-query integration assertion for `台積電的碳中和目標是什麼` that checks citation-ready bounded evidence when required environment variables are present.
- [ ] Document the Claude Desktop MCP configuration in project docs or module docstrings if no broader README exists yet.
- [ ] Run `openspec validate add-claude-esg-mcp-server --strict` or the equivalent available validation command.
- [ ] Run the full available test suite and update `openspec/changes/add-claude-esg-mcp-server/tasks.md` checkboxes for completed work.
- [ ] Summarize implemented behavior, test evidence, known limitations, and deferred Phase 2 items.

## Notes

- The current workspace is being prepared for Git/GitHub version control.
- Real Chroma access must use a writable temp copy during tests because opening the original index path currently raises a read-only database error.
