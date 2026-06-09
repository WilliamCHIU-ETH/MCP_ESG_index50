# ADR-003: MCP Server as a Thin Consumer Adapter

**Date:** 2026-06-09
**Status:** Proposed — accepted for Phase 2 design

## Context

Phase 1 MCP server contains retrieval logic directly (embedding call, ChromaDB query, result
formatting). This couples the transport layer (MCP/stdio) to the storage layer (ChromaDB).
Any storage migration or retrieval change requires touching the MCP server.

## Decision

In Phase 2, the MCP server SHALL be a thin adapter only. All retrieval logic (embedding,
vector search, reranking, result formatting) moves to an independent Retrieval layer with a
stable Python interface. The MCP tool handler calls the Retrieval layer and returns its output.

## Consequences

**Positive:** Retrieval layer can be tested independently of MCP transport. Storage migrations
are isolated to the Retrieval layer. Future adapters (REST, gRPC) can reuse the same layer.

**Negative:** Additional abstraction layer; slightly more files to navigate.

## Interface Contract (to be defined)

```python
class RetrievalService:
    def search(self, query: str, company: str | None, top_k: int) -> list[EvidenceChunk]:
        ...
```

The MCP handler calls `RetrievalService.search()` and serializes the result. No ChromaDB imports
in the MCP server module.
