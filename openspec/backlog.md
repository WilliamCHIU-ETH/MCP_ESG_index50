# ESG MCP Backlog

本專案的 OpenSpec 設定沒有獨立的 backlog 指令。可執行的工作項以 `openspec/changes/*` 為準，本檔案是決定「接下來要建立哪個 change」的 roadmap。

## Backlog 原則

- 本檔案是純 roadmap：只記「項目名稱 + 目的 + 進入條件」。決策只存在於
  `docs/decisions/`（ADR）；此處絕不重述決策狀態，只放連結。
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
- `host-mcp-service` — 遠端 MCP server 上線於 Cloudflare Workers + Vectorize。
  2026-10-28 結案，見 [ADR-005](../docs/decisions/005-cloudflare-serverless.md)，tag `v2.0.0`。
- `document-claude-installation` — 已由 [worker/README.md](../worker/README.md)
  涵蓋（部署、secret、加成 custom connector）。

## 已取代（Superseded）

- `migrate-storage-and-embedding-v2` — 原計畫遷移至 pgvector 並以 Gemini Embedding 2
  （768d）re-embed。已被 [ADR-005](../docs/decisions/005-cloudflare-serverless.md) 取代：
  遠端版改用 Vectorize，沿用 OpenAI 向量截斷至 256 維，不做 pgvector + Gemini。

## 現在（Now）

### `run-mcp-retrieval-validation`

目的：以真實問題集驗證遠端版（256 維）的檢索品質。

進入條件：
- 遠端 MCP server 已上線（已達成）。

預期範圍：
- 用真實 ESG 問題集跑 `scripts/quality_check.py`，比較 1536 維與 256 維的 top-k。
  目前只有代理指標：top-5 重疊率不限公司 72%、限定公司 80%。
- 20–30 題 smoke test 與引用品質審查。
- 失敗分類：tool 選擇、檢索品質、引用格式、context 長度。

### `clean-garbled-chunks`

目的：找出並處理 PDF 抽取造成的亂碼 chunk（例如凱基金控 p.159）。

進入條件：
- 無。

預期範圍：
- 以控制字元比例等規則偵測亂碼 chunk。
- 從 Vectorize 移除，或在 metadata 標記。
- 回報受影響的公司與頁數。

## 接下來（Next）

### `evaluate-reranker`

目的：評估是否加入 reranker 或分數門檻。

進入條件：
- `run-mcp-retrieval-validation` 完成（有 baseline）。

預期範圍：
- cross-encoder 與 score threshold 的小規模比較。
- 對 Worker CPU 與延遲的影響（目前 `tools/call` CPU 中位數約 60 ms）。

## 之後（Later）

注意：Vectorize Free 儲存上限 500 萬維，目前已用約 439 萬維，只剩約 56 萬維
（約 2,000 段 256 維 chunk）。新增語料前需先決定升級方案或縮減維度。

### `rebuild-corpus-from-pdfs`

目的：當新年度、新報告書或新 embedding 策略需要時，從來源 PDF 重建語料庫。

進入條件：
- 來源 PDF 清單與報告年度政策已定義。

預期範圍：
- 公司／報告書 manifest。
- PDF 下載或本地匯入 pipeline。
- 文字抽取與 chunking。
- Embedding 產生。
- Index 建置（依 ADR-002 使用版本化 index 名稱）。
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

## 明確延後（Explicitly Deferred）

- UI 或 dashboard。
- 後端直接產生 ESG 最終答案。
- 使用者上傳 PDF 的 ingestion。
- MCP 原型可用前的完整 RAGAS benchmark。
- Claude-first 體驗成熟前的 agent-agnostic 工具封裝。
