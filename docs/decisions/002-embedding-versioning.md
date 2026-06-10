# ADR-002: Embedding Model Version Governance

**Date:** 2026-06-09
**Status:** Accepted

## Context

Phase 1 使用 OpenAI `text-embedding-3-small`（1536 維度）。索引與查詢的 embedding 必須使用相同的模型版本；若模型被棄用或升級，語料庫就必須重新 embed——對 17,144 個 chunk 而言是不可忽視的成本。

Phase 2 將向量儲存遷移至 pgvector（ADR-001），這是在語料庫重建之前一併升級 embedding 模型的自然時機點。

## Decision

**Adopt Gemini Embedding 2 (`gemini-embedding-2`) as the Phase 2 embedding model.**

- 將模型字串固定於設定檔（`EMBEDDING_MODEL=gemini-embedding-2`），禁止靜默自動升級。
- 以版本化 collection 名稱（`esg_reports_50_v2`）管理語料庫。遷移期間同時維護新舊兩份語料庫；舊語料庫在新版通過驗證後才刪除。
- 使用 **768 維度**（從 3072 維空間進行 MRL 截斷），在我們 17,144 個 chunk 的規模下平衡 retrieval 品質與 pgvector 儲存及索引大小。

> **查證註記（2026-06-10）**：下表「Status: Generally Available」與實況不符。
> 截至 2026-06，Gemini Embedding 2 仍為 **public preview**（2026-03-10 發布），
> 實際可呼叫的模型字串為 **`gemini-embedding-2-preview`**，preview 期間 Google
> 可能調整定價與行為。GA 前 `EMBEDDING_MODEL` 應固定為 preview 字串，並在 GA
> 後以 amendment 更新本表。MTEB 數字亦待覆核（第三方評測顯示 3072d 約 68.2、
> 768d 約 68.0，非 69.9）。本決策（選用該模型、768d）不變，僅規格表需修正。

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

1. **Pin model string in config, block upgrades** — 最安全，但會累積技術債。
2. **Version the collection name** (`esg_reports_50_v2`) — 遷移期間允許同時維護多份語料庫。
3. **Abstract embedding model behind an interface** — 更具未來彈性，但現在引入多一層抽象。

**Chosen:** Options 1 + 2 combined。Option 3 延後至 Phase 3，待多 provider 支援需求出現時再處理。

## Upgrade Trigger Policy

滿足以下**任一條件**時，啟動 embedding 模型升級流程：

1. **Deprecation notice** — provider 宣布 `gemini-embedding-2` 的終止支援日期。
2. **Quality regression** — 在 ESG 驗證集上的 retrieval 評估（NDCG@10）相較 Phase 2 baseline 下降超過 5 個百分點。
3. **Dimension incompatibility** — 必要的下游功能（例如跨模態搜尋）無法由當前模型維持服務。

僅節省成本**不足以**作為觸發條件；re-embed 的成本與停機風險必須與節省效益相互權衡。

## Corpus Rebuild Approval

語料庫重建是 retrieval layer 的破壞性變更，需要滿足以下條件：

1. **Owner approval** ([@WilliamCHIU-ETH](https://github.com/WilliamCHIU-ETH)) — 決策須以新 ADR 或 ADR amendment 記錄。
2. **Validation gate** — 新語料庫必須在 ESG 驗證查詢集上達到 NDCG@10 ≥ baseline，才能刪除舊語料庫。
3. **Rollback window** — 切換後至少保留前一版本化語料庫 7 天。

## Consequences

- Phase 2 的 re-embed 作業以 `gemini-embedding-2`（768 維度）為目標，寫入 `esg_reports_50_v2`。
- 查詢路徑必須從設定檔讀取 `EMBEDDING_MODEL`；程式碼中硬編碼模型字串視為建置錯誤。
- 768 維的 pgvector 索引使用 `vector(768)` 欄位型別；此設定必須反映在 schema 遷移腳本中。
- 未來的模型替換遵循版本化 collection 的模式，並需要補充一份 ADR amendment。
- 驗證分段（2026-06-10）：本 ADR 的 validation gate 在分段驗證的 Stage 2 執行，
  比較對象為 Stage 1 的 pgvector + OpenAI 1536d baseline——詳見 ADR-001 Amendment。
