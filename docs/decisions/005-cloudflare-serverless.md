# ADR-005: Cloudflare Workers + Vectorize as the Remote Deployment

**Date:** 2026-10-28
**Date decided:** 2026-10-28
**Status:** Accepted
**Supersedes:** [ADR-001](001-pgvector-vs-chroma.md)（遠端部署的向量儲存）
**Amends:** [ADR-002](002-embedding-versioning.md)、[ADR-004](004-remote-transport-and-auth.md)

## Context

ADR-004 的 true north 是「貼一個 URL 就能查」的遠端 MCP server。ADR-001／002 原本規劃
pgvector + Gemini Embedding 768 維，前提是要先完成 re-embed 與代管 Postgres，成本與
維運都不低。實際需求是個人使用、零固定成本、語料庫為公開 ESG 報告（17,144 chunks、
50 家公司，OpenAI `text-embedding-3-small` 1536 維）。

2026-10-28 在 Cloudflare Workers **Free** 方案上實測了兩種 Python 寫法的每請求 CPU
（`wrangler tail`，單位 ms，每方法 n = 21）：

| 項目 | A：官方 `mcp` 2.3.0 SDK | B：手寫最小協定層（stdlib `json`） |
|---|---|---|
| bundle（gzip） | 5,244 KiB | 33 KiB |
| 首請求 CPU / wall | 800 / 820 | 36 / 37 |
| `server/discover` CPU 中位數 / 最大 | 334 / 1,154 | 19 / 61 |
| `tools/list` CPU 中位數 / 最大 | 22 / 1,160 | 19 / 61 |
| `tools/call`（假資料）CPU 中位數 / 最大 | 35 / 1,208 | 16 / 76 |
| 超過 10 ms 的請求 | 57 / 63 | 49 / 63 |
| 1102（CPU 超限） | 0 | 0 |

A 每次落到新 isolate 都要重新載入 SDK，反覆出現 200–1,200 ms 尖峰；B 最差 76 ms。
B 回傳預先序列化好的字串，中位數仍有 16–19 ms，這是 Python Workers 每請求本身的底線。

## Decision

遠端版採用 **一個 Cloudflare Python Worker（手寫最小 MCP 協定層）+ 一個 Vectorize index**，
部署在 Workers Free 方案。stdio + ChromaDB（`src/claude_esg_mcp/`）保留為本機開發模式，
程式不動。

- **協定：** MCP 2026-07-28 無狀態（`POST`，`server/discover`、`tools/list`、
  `tools/call`，檢查 `MCP-Protocol-Version`／`Mcp-Method`／`Mcp-Name`），另支援舊版
  無狀態 `initialize`。不使用官方 SDK（CPU 與 bundle 大小見上表）。
- **向量儲存：** Vectorize `esg-reports-256`（cosine，`company` metadata index）。
  沿用既有 1536 維向量，取前 256 維後 L2 正規化（Matryoshka 截斷），不重新 embed。
- **查詢 embedding：** OpenAI `text-embedding-3-small`，`dimensions=256`，
  與索引同一模型、同一截斷方式。
- **輸出：** 與 v1 `RetrievalService._format_result` 相同欄位，另放 `structuredContent`。
  score 維持 v1 定義：Chroma 對單位向量的平方 L2 = 2 − 2cos，`score = 1 / (1 + 2 − 2cos)`。
- **存取控制：** 路徑帶隨機 token（`/mcp/<MCP_PATH_TOKEN>`，Worker secret），不符一律
  404，且不會呼叫 OpenAI。OAuth 延後。

## Options Considered

| 選項 | 結論 | 理由 |
|---|---|---|
| A. Python Worker + 官方 SDK | 否決 | gzip 5.2 MB；冷 isolate 200–1,200 ms CPU |
| B. Python Worker + 手寫協定層 | **採用** | 33 KiB；CPU 中位數 16–19 ms；沿用 Python 與 v1 格式 |
| C. TypeScript Worker（官方 TS SDK） | 未實測，不採用 | 預期 CPU 更低，但需改寫成另一種語言；B 已可用 |
| D. VPS／本機 + Cloudflare Tunnel 跑 v1 | 否決 | 需要常駐主機與維運；違背「零固定成本、關機也能用」 |
| E. pgvector 代管（ADR-001 原案） | 延後 | 需代管 Postgres 與 re-embed；目前規模不需要 SQL join |

## Evidence

### 256 維截斷品質

本機以 300 筆語料本身的 1536 維向量當查詢，比較精確 top-5：

| 範圍 | 平均 top-5 重疊 | 至少 1 筆相同 | 最差 |
|---|---|---|---|
| 不限公司 | 72% | 299/300 | 0% |
| 同一家公司 | 80% | 300/300 | 20% |

`scripts/quality_check.py` 可在有 OpenAI key 時改用真實問題重跑。

### 線上 CPU（實際 OpenAI + Vectorize，2026-10-28）

| 方法 | n | CPU 中位數 / 最大（ms） | wall 中位數 / 最大（ms） |
|---|---|---|---|
| `tools/call` | 20 | 59.5 / 141 | 488 / 727 |
| `server/discover` | 10 | 14.5 / 38 | 15.5 / 39 |
| `tools/list` | 10 | 17.5 / 51 | 18 / 53 |

40 次全部成功，無 1102、無例外。

## Cost and Abuse Controls

- **Cloudflare：** Free 方案不會因流量收費。帳號每日 10 萬次請求上限，被打滿只會停擺到
  UTC 午夜。Vectorize 儲存 17,144 × 256 ≈ 439 萬維（Free 上限 500 萬維）。
- **OpenAI：** 每次查詢約 0.000001 美元；帳戶預付 5 美元並關閉自動儲值作為硬上限，key 建議
  設為只允許 embeddings 的 restricted key。
- **防濫用：** 路徑 token（不符 → 404，不碰 OpenAI）、query ≤ 500 字、body ≤ 16 KiB。
  安全審查見 [docs/security-review.md](../security-review.md)。

## Known Limitations

1. **CPU 超過 Free 名目 10 ms：** `tools/call` 中位數約 60 ms。實測未被擋，但不保證
   Cloudflare 日後不嚴格執行；屆時改 Workers Paid（每月 5 美元）或改寫成 TypeScript。
2. **Vectorize 儲存接近 Free 上限：** 剩約 56 萬維，大約只能再加 2,000 筆 256 維 chunk。
3. **部分 chunk 為 PDF 抽取亂碼：** 例如凱基金控 p.159，含控制字元。這是 ingestion 的
   既有問題，截斷不會改善也不會惡化。
4. **路徑 token 不是使用者驗證：** 無法 per-user 限流或撤銷單一使用者；外流時只能換 token。
5. **沒有 Retrieval layer 抽象：** Worker 內直接呼叫 OpenAI 與 Vectorize。ADR-003 的介面
   合約在 v1 已存在；遠端版刻意保持單檔，以壓低 CPU 與 bundle。

## Consequences

- ADR-001 由本 ADR 取代（遠端部署的向量儲存改為 Vectorize）。pgvector 只在需要 SQL join
  或超過 Vectorize 上限時重新評估。
- ADR-002 的 Gemini 768 維遷移暫緩；遠端版固定 `text-embedding-3-small` + 256 維。
  若要換模型，仍依 ADR-002 的 rebuild 規則，新建版本化 index（例如 `esg-reports-<model>-<dims>`）。
- ADR-004 的 transport 改以 MCP 2026-07-28 無狀態 HTTP 實作；auth 以路徑 token 起步，OAuth 延後。
- esg-platform-v2 的畢業條件「遠端 client 只靠 URL 完成 `search_esg_reports`」已達成。

## OPEN

- OAuth（MCP authorization）何時導入：等到需要多使用者或 per-user 配額時。
- 是否把 `tools/call` CPU 降到 10 ms 以下（TypeScript 改寫或 Paid 方案）。
- 以真實問題集（`scripts/quality_check.py`）補一次 1536 對 256 的品質比較。

## References

- 部署與操作：[worker/README.md](../../worker/README.md)
- 安全審查：[docs/security-review.md](../security-review.md)
- 相關決策：[ADR-003](003-mcp-as-adapter.md)、[ADR-004](004-remote-transport-and-auth.md)
