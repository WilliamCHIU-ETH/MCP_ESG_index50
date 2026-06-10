# esg-platform-v2

**Status:** Draft
**Supersedes:** claude-esg-mcp-retrieval (Phase 1)
**Created:** 2026-06-09

## Problem

Phase 1 validated that Claude can call a local MCP server to retrieve ESG evidence. However, the
current implementation has three structural issues that block production readiness: (1) the
ChromaDB index is a local file with no ingestion pipeline, (2) startup time includes index mutation
that belongs in a separate ingestion job, and (3) the MCP tool is tightly coupled to the storage
layer with no retrieval abstraction.

## Goals

- Define a canonical schema covering the 9 core ESG entities (company, report, section, chunk,
  embedding, citation, query, result, evaluation).
- Separate the system into three independent layers: Ingestion, Retrieval, and Consumer (MCP adapter).
- Move all startup mutations out of the query-serving path.
- Document architecture decisions as ADRs before implementation begins.
- **True north: a publicly hosted, multi-user remote MCP server over Streamable HTTP.** Anyone
  can paste a URL into Claude Desktop and query the ESG corpus — no local setup, no local index,
  no local environment. Local stdio remains the development transport. (Transport and auth
  decisions: ADR-004.)

## Non-Goals

- UI or web dashboard
- Backend-generated final ESG answers (Claude remains the synthesis layer)
- Agent-agnostic packaging before Claude-first usage is validated
- Full RAGAS benchmark re-run in Phase 2 scope

## Architecture Overview

Three layers, each independently testable:

**Ingestion layer** — offline pipeline: PDF → chunk → embed → store. Runs as a separate job,
not on server startup.

**Retrieval layer** — query-time: embed query (Gemini Embedding 2, 768 dims; see ADR-002) → vector search (pgvector; see ADR-001) → rerank (Phase 2+) → return
top-k with metadata. Storage-agnostic interface; concrete implementation behind an adapter.

**Consumer layer** — MCP server acts as a thin adapter that calls the Retrieval layer. No
retrieval logic lives in the MCP server itself. Two transport adapters share the same Retrieval
layer: stdio (local development) and Streamable HTTP (hosted, multi-user; see ADR-004).
Auth and rate limiting are Consumer-layer responsibilities and must not leak into the
Retrieval layer.

## Architecture Decisions

- [ADR-001](../../docs/decisions/001-pgvector-vs-chroma.md) — pgvector as vector store (Accepted)
- [ADR-002](../../docs/decisions/002-embedding-versioning.md) — Gemini Embedding 2, 768 dims (Accepted)
- [ADR-003](../../docs/decisions/003-mcp-as-adapter.md) — MCP as thin adapter (Proposed)
- [ADR-004](../../docs/decisions/004-remote-transport-and-auth.md) — remote transport & auth (Proposed)

## Open Questions

- [ ] ADR-003: RetrievalService interface contract — finalize before Phase 2 implementation begins
- [ ] ADR-004: auth model — OAuth vs API key vs unauthenticated-with-rate-limit
- [ ] ADR-004: rate limiting strategy for a public multi-user endpoint
- [ ] RetrievalService statelessness — concurrency constraints for multi-user serving
  (no per-session state in the Retrieval layer)
- [ ] Reranker strategy — cross-encoder vs score threshold; in Phase 2 scope or later?
- [ ] Corpus refresh cadence — annual, triggered, or manual?

## Graduation Criteria (Beta → Stable)

- All 5 Phase 2 entry conditions met (see project-brief.md)
- Retrieval layer has its own test suite independent of MCP
- At least one ADR per open question above is closed
- A remote MCP client can complete a `search_esg_reports` tool call given only a URL
  (no local setup)
