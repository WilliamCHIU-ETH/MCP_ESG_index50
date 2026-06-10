# ESG MCP Backlog

本專案的 OpenSpec 設定沒有獨立的 backlog 指令。可執行的工作項以 `openspec/changes/*` 為準，本檔案是決定「接下來要建立哪個 change」的 roadmap。

## Backlog 原則

- 本檔案是純 roadmap：只記「項目名稱 + 目的 + 進入條件」。決策只存在於
  `docs/decisions/`（ADR）；此處絕不重述決策狀態，只放連結。
- 在 Claude 能穩定使用本地 MCP tool 之前，Phase 1 範圍保持窄。
- 每一個連貫的實作切片對應一個 OpenSpec change。
- ADR 明確決定時，允許**工作**綑綁；但**驗證**不可混合。每個遷移變數
  （儲存、embedding 模型、代管部署、tool 合約）必須有獨立的驗證關卡，
  讓任何指標退化都能歸因到單一變數。
- backlog 項目只有在 proposal/design/spec/tasks 都準備好時，才升級為
  `openspec/changes/<name>/`。

> 原則沿革：原本的「不可混合遷移」規則與 ADR-001/ADR-002 決定的綑綁遷移衝突
> （2026-06-10 標記為「Known Inconsistency」）。同日由 owner 決議解決：
> **工作綑綁、驗證分段**——見下方 `migrate-storage-and-embedding-v2`。

## 已完成（Done）

- `add-claude-esg-mcp-server` — Phase 1 MVP（MCP server、ChromaDB 向量檢索、
  18 個 unit test、integration 通過）。2026-06-09 結案。

## 現在（Now）

### `run-mcp-retrieval-validation`

目的：驗證 MCP 檢索行為是否保留舊有 vector-only 的優勢。

進入條件：
- Phase 1 MCP server 可在本地執行。

預期範圍：
- 20–30 題 smoke test。
- 小規模 vector-only vs 其他檢索方式比較。
- 引用品質審查。
- 失敗分類：tool 選擇、檢索品質、引用格式、context 長度。

## 接下來（Next）

### `document-claude-installation`

目的：讓本地 Claude MCP 安裝設定可重現。

進入條件：
- MCP server 進入點穩定。

預期範圍：
- Claude Desktop 設定範例。
- 環境變數。
- 本地 index 路徑的預期行為。
- 疑難排解：缺 API key、缺 index、embedding 維度不符。

## 之後（Later）

### `migrate-storage-and-embedding-v2`

目的：將向量儲存從 ChromaDB 遷移至 pgvector，並以 Gemini Embedding 2（768d）
重新 embed 語料庫——工作綑綁為一個 effort，但採**分段驗證**。

依據 [ADR-001](../docs/decisions/001-pgvector-vs-chroma.md) 與
[ADR-002](../docs/decisions/002-embedding-versioning.md)。本項目取代原先的
`compare-google-embedding-pipeline` 與 `migrate-index-to-pgvector` 兩個項目。

進入條件：
- `run-mcp-retrieval-validation` 完成（建立檢索 baseline）。

分段驗證（單一變數控制）：
1. **Stage 1 — 儲存變數**：將現有 OpenAI 1536d 向量原樣複製進 pgvector
   （不重新 embed），對 ChromaDB baseline 跑 parity test。此階段的任何差異
   只可能來自儲存／索引層。
2. **Stage 2 — 模型變數**：以 Gemini Embedding 2（768d）re-embed 至版本化
   collection `esg_reports_50_v2`，依 ADR-002 validation gate 對 Stage 1
   baseline 跑 NDCG@10。此階段的任何差異只可能來自 embedding 模型。

預期範圍：
- PostgreSQL schema：company、report、chunk、page、content、embedding、metadata。
- 向量搜尋查詢實作。
- Stage 1 向量複製 + parity test；Stage 2 re-embed pipeline + NDCG@10 關卡。
- 依 ADR-002 的 rollback window 與舊語料庫保留政策。

### `rebuild-corpus-from-pdfs`

目的：當新年度、新報告書或新 embedding 策略需要時，從來源 PDF 重建語料庫。

進入條件：
- 來源 PDF 清單與報告年度政策已定義。

預期範圍：
- 公司／報告書 manifest。
- PDF 下載或本地匯入 pipeline。
- 文字抽取與 chunking。
- Embedding 產生。
- Index 建置。
- 語料庫盤點報告。

### `add-corpus-refresh-workflow`

目的：支援 ESG 報告書的後續更新，不必每次手動一次性重建。

進入條件：
- 重建 pipeline 已存在且可靠。

預期範圍：
- 報告來源 manifest。
- 版本化語料庫 metadata。
- 增量更新策略。
- 檢索與引用品質的回歸檢查。

### `host-mcp-service`

目的：在本地 Claude 使用驗證後，評估代管部署。

進入條件：
- 本地 MCP 有用且可重現（`run-mcp-retrieval-validation` 完成）。
- [ADR-003](../docs/decisions/003-mcp-as-adapter.md) 定案。

預期範圍：
- 部署目標。
- 認證與速率限制。
- 資料存取模型。
- 成本模型。
- 維運監控。

## 明確延後（Explicitly Deferred）

- UI 或 dashboard。
- 後端直接產生 ESG 最終答案。
- 使用者上傳 PDF 的 ingestion。
- MCP 原型可用前的完整 RAGAS benchmark。
- Claude-first 體驗成熟前的 agent-agnostic 工具封裝。
