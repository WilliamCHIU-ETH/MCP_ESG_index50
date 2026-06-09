# ADR-001: pgvector vs ChromaDB as Vector Store

**Date:** 2026-06-09
**Date decided:** 2026-06-09
**Status:** Accepted

## Context

Phase 1 uses a local ChromaDB file index. ChromaDB works for local development but has no
managed hosted offering, limited RBAC, and no SQL join capability for metadata queries.
pgvector runs inside PostgreSQL and enables SQL-native metadata filtering alongside vector search.

## Decision

Adopt pgvector (PostgreSQL extension) as the Phase 2 vector store.
Primary driver: managed cloud deployability. ChromaDB has no viable hosted offering
for production use. pgvector runs on any managed PostgreSQL (Supabase, Neon, RDS).
Secondary: SQL-native metadata filtering enables future joins without an ORM layer.
Migration cost accepted: corpus will be re-embedded as part of the Gemini embedding
migration (see ADR-002), so the incremental pgvector migration cost is near-zero.

## Options Considered

| Criterion | ChromaDB | pgvector |
|---|---|---|
| Local dev simplicity | ✓ simple | requires Postgres |
| Hosted deployment | ✗ limited | ✓ managed Postgres |
| SQL metadata joins | ✗ | ✓ |
| Migration cost | — | full re-embed if schema changes |
| Operational overhead | low | medium |

## Consequences

- Phase 2 corpus must be migrated from ChromaDB to pgvector; this is absorbed into the
  Gemini embedding re-embed job (ADR-002) to avoid a separate migration step.
- Retrieval parity tests must be re-run against the pgvector baseline before the old
  ChromaDB index is retired.
- Hosted deployment is now unblocked; any managed PostgreSQL provider is a valid target.
