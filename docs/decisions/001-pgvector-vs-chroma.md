# ADR-001: pgvector vs ChromaDB as Vector Store

**Date:** 2026-06-09
**Date decided:** 2026-06-09
**Status:** Accepted

## Context

Phase 1 使用本地 ChromaDB 檔案索引。ChromaDB 適合本地開發，但沒有可用的代管服務、RBAC 有限，且無法對 metadata 進行 SQL join 查詢。pgvector 以 PostgreSQL extension 的形式運作，可在向量搜尋的同時進行 SQL 原生的 metadata 過濾。

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

- Phase 2 語料庫需從 ChromaDB 遷移至 pgvector；此工作已合併入 Gemini embedding 的 re-embed 作業（ADR-002），避免額外的獨立遷移步驟。
- 在退役舊 ChromaDB 索引前，必須針對 pgvector baseline 重新執行 retrieval 一致性測試。
- 代管部署不再受阻；任何代管 PostgreSQL 服務商均可作為目標部署環境。
