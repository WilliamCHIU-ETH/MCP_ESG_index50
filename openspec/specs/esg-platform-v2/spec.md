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
retrieval logic lives in the MCP server itself.

## Architecture Decisions

- [ADR-001](../../docs/decisions/001-pgvector-vs-chroma.md) — pgvector as vector store (Accepted)
- [ADR-002](../../docs/decisions/002-embedding-versioning.md) — Gemini Embedding 2, 768 dims (Accepted)
- [ADR-003](../../docs/decisions/003-mcp-as-adapter.md) — MCP as thin adapter (Proposed)

## Open Questions

- [ ] ADR-003: RetrievalService interface contract — finalize before Phase 2 implementation begins
- [ ] Reranker strategy — cross-encoder vs score threshold; in Phase 2 scope or later?
- [ ] Corpus refresh cadence — annual, triggered, or manual?

## Graduation Criteria (Beta → Stable)

- All 5 Phase 2 entry conditions met (see project-brief.md)
- Retrieval layer has its own test suite independent of MCP
- At least one ADR per open question above is closed
