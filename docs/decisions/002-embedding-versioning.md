# ADR-002: Embedding Model Version Governance

**Date:** 2026-06-09
**Status:** Open

## Context

Phase 1 uses OpenAI `text-embedding-3-small` (1536 dimensions). The index and query embedding
must use the same model version. If the model is deprecated or upgraded, the corpus must be
re-embedded — a non-trivial cost for 17,144 chunks.

## Decision

TBD — to be decided before any embedding model change is made.

## Options Considered

1. **Pin model string in config, block upgrades** — safest, but creates technical debt.
2. **Version the collection name** (`esg_reports_50_v2`) — allows parallel corpora during migration.
3. **Abstract embedding model behind an interface** — future-proof but adds indirection now.

## Consequences

A governance policy must be in place before any Phase 2 embedding change. The chosen option
determines whether re-embedding requires downtime or can be done incrementally.

## Open Questions

- What is the trigger for an embedding model upgrade? (cost, quality regression, deprecation notice)
- Who approves a corpus rebuild?
