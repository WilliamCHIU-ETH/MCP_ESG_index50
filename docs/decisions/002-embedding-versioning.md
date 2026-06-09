# ADR-002: Embedding Model Version Governance

**Date:** 2026-06-09
**Status:** Accepted

## Context

Phase 1 uses OpenAI `text-embedding-3-small` (1536 dimensions). The index and query embedding
must use the same model version. If the model is deprecated or upgraded, the corpus must be
re-embedded — a non-trivial cost for 17,144 chunks.

Phase 2 migrates the vector store to pgvector (ADR-001). This is a natural point to also
upgrade the embedding model before the corpus is rebuilt.

## Decision

**Adopt Gemini Embedding 2 (`gemini-embedding-2`) as the Phase 2 embedding model.**

- Pin the model string in config (`EMBEDDING_MODEL=gemini-embedding-2`). No silent auto-upgrades.
- Version the collection name: `esg_reports_50_v2`. Parallel corpora are maintained during any future migration window; the old corpus is dropped only after the new one passes validation.
- Use **768 dimensions** (MRL truncation from the 3072-dim space). This balances retrieval quality against pgvector storage and index size for our 17,144-chunk corpus.

## Model Specification

| Property        | Value                                   |
|-----------------|-----------------------------------------|
| Model string    | `gemini-embedding-2`                    |
| Provider        | Google DeepMind / Gemini API            |
| Status          | Generally Available                     |
| Input modalities| Text, Image, Video, Audio, Documents    |
| Max input tokens| 8,192                                   |
| Dimension range | 128 – 3072 (Matryoshka / MRL)           |
| Chosen dimension| **768**                                 |
| Multilingual    | 100+ languages                          |
| MTEB (Multilingual) mean | 69.9 (state-of-the-art)      |

## Options Considered

1. **Pin model string in config, block upgrades** — safest, but creates technical debt.
2. **Version the collection name** (`esg_reports_50_v2`) — allows parallel corpora during migration.
3. **Abstract embedding model behind an interface** — future-proof but adds indirection now.

**Chosen:** Options 1 + 2 combined. Option 3 deferred to Phase 3 when multi-provider support becomes necessary.

## Upgrade Trigger Policy

An embedding model upgrade is initiated when **any one** of the following conditions is met:

1. **Deprecation notice** — provider announces end-of-life for `gemini-embedding-2` with a deadline.
2. **Quality regression** — retrieval evaluation (NDCG@10 on the ESG validation set) drops more than 5 percentage points from the Phase 2 baseline.
3. **Dimension incompatibility** — a required downstream feature (e.g., cross-modal search) cannot be served by the current model.

Cost reduction alone is **not** a sufficient trigger; the re-embed cost and downtime risk must be weighed against the savings.

## Corpus Rebuild Approval

The corpus rebuild is a breaking change to the retrieval layer. It requires:

1. **Owner approval** ([@WilliamCHIU-ETH](https://github.com/WilliamCHIU-ETH)) — decision recorded as a new ADR or ADR amendment.
2. **Validation gate** — the new corpus must achieve NDCG@10 ≥ baseline on the ESG validation query set before the old corpus is deleted.
3. **Rollback window** — the previous versioned corpus is retained for at least 7 days post-cutover.

## Consequences

- Phase 2 re-embed job targets `gemini-embedding-2` at 768 dimensions into `esg_reports_50_v2`.
- Query path must read `EMBEDDING_MODEL` from config; hardcoded model strings are a build error.
- The 768-dim pgvector index uses `vector(768)` column type; this must be reflected in the schema migration.
- Future model swaps follow the versioned-collection pattern and require an ADR amendment.
