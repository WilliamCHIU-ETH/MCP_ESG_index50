# ADR-001: pgvector vs ChromaDB as Vector Store

**Date:** 2026-06-09
**Date decided:** 2026-06-09
**Status:** Accepted

## Context

Phase 1 使用本地 ChromaDB 檔案索引。ChromaDB 適合本地開發，但沒有可用的代管服務、RBAC 有限，且無法對 metadata 進行 SQL join 查詢。pgvector 以 PostgreSQL extension 的形式運作，可在向量搜尋的同時進行 SQL 原生的 metadata 過濾。

## Decision

採用 pgvector（PostgreSQL extension）作為 Phase 2 的向量儲存方案。
主要驅動因素：代管雲端部署能力。ChromaDB 沒有可用於正式環境的代管服務；pgvector 可在任何代管 PostgreSQL 上運作（Supabase、Neon、RDS）。
次要因素：SQL 原生的 metadata 過濾，未來可直接進行 join 查詢，無需額外 ORM 層。
遷移成本可接受：語料庫將在 Gemini embedding 遷移作業（見 ADR-002）中一併重新 embed，pgvector 的額外遷移成本接近於零。

## Options Considered

| 評估標準 | ChromaDB | pgvector |
|---|---|---|
| 本地開發簡易度 | ✓ 簡單 | 需要 Postgres |
| 代管部署 | ✗ 有限 | ✓ 代管 Postgres |
| SQL metadata join | ✗ | ✓ |
| 遷移成本 | — | schema 變更須完整 re-embed |
| 運維負擔 | 低 | 中 |

## Consequences

- Phase 2 語料庫需從 ChromaDB 遷移至 pgvector；此工作已合併入 Gemini embedding 的 re-embed 作業（ADR-002），避免額外的獨立遷移步驟。
- 在退役舊 ChromaDB 索引前，必須針對 pgvector baseline 重新執行 retrieval 一致性測試。
- 代管部署不再受阻；任何代管 PostgreSQL 服務商均可作為目標部署環境。
