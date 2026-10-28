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

**Retrieval layer** — query-time: embed query (remote: OpenAI `text-embedding-3-small` at 256 dims; see ADR-005, amending ADR-002) → vector search (remote: Cloudflare Vectorize; see ADR-005, superseding ADR-001) → rerank (Phase 2+) → return
top-k with metadata. Storage-agnostic interface; concrete implementation behind an adapter.

**Consumer layer** — MCP server acts as a thin adapter that calls the Retrieval layer. No
retrieval logic lives in the MCP server itself. Two transport adapters share the same Retrieval
layer: stdio (local development) and Streamable HTTP (hosted, multi-user; see ADR-004).
Auth and rate limiting are Consumer-layer responsibilities and must not leak into the
Retrieval layer.

## Architecture Decisions

- [ADR-001](../../docs/decisions/001-pgvector-vs-chroma.md) — pgvector as vector store (Superseded by ADR-005)
- [ADR-002](../../docs/decisions/002-embedding-versioning.md) — Gemini Embedding 2, 768 dims (Accepted, amended by ADR-005)
- [ADR-003](../../docs/decisions/003-mcp-as-adapter.md) — MCP as thin adapter (Accepted)
- [ADR-004](../../docs/decisions/004-remote-transport-and-auth.md) — remote transport & auth (Accepted with amendments)
- [ADR-005](../../docs/decisions/005-cloudflare-serverless.md) — Cloudflare Workers + Vectorize remote deployment (Accepted)

## Open Questions

- [x] ADR-003: RetrievalService interface contract — Accepted 2026-10-28 (v1 `RetrievalService`;
  remote Worker mirrors the same output contract)
- [x] ADR-004: auth model — secret path token for now, OAuth deferred (ADR-004 amendment, ADR-005)
- [x] ADR-004: rate limiting strategy — request-size limits + Workers Free daily cap + prepaid OpenAI
  budget; per-IP WAF limits deferred
- [x] RetrievalService statelessness — remote Worker is fully stateless (MCP 2026-07-28)
- [ ] Reranker strategy — cross-encoder vs score threshold; in Phase 2 scope or later?
- [ ] Corpus refresh cadence — annual, triggered, or manual?

## Graduation Criteria (Beta → Stable)

- All 5 Phase 2 entry conditions met (see project-brief.md)
- Retrieval layer has its own test suite independent of MCP
- At least one ADR per open question above is closed
- [x] A remote MCP client can complete a `search_esg_reports` tool call given only a URL
  (no local setup) — **met 2026-10-28** by the Cloudflare Worker (ADR-005, `worker/`)
