# ADR-001: pgvector vs ChromaDB as Vector Store

**Date:** 2026-06-09
**Status:** Open

## Context

Phase 1 uses a local ChromaDB file index. ChromaDB works for local development but has no
managed hosted offering, limited RBAC, and no SQL join capability for metadata queries.
pgvector runs inside PostgreSQL and enables SQL-native metadata filtering alongside vector search.

## Decision

TBD — to be decided before Phase 2 implementation begins.

## Options Considered

| Criterion | ChromaDB | pgvector |
|---|---|---|
| Local dev simplicity | ✓ simple | requires Postgres |
| Hosted deployment | ✗ limited | ✓ managed Postgres |
| SQL metadata joins | ✗ | ✓ |
| Migration cost | — | full re-embed if schema changes |
| Operational overhead | low | medium |

## Consequences

If ChromaDB: Phase 2 stays local-only; hosted deployment blocked until a later ADR revisits.
If pgvector: corpus must be migrated; retrieval tests must be re-run for parity.

## Open Questions

- Is hosted deployment a Phase 2 goal or Phase 3?
- What is the acceptable migration downtime window?
