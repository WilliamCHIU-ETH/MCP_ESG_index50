# esg-mcp Worker（遠端版）

一個 Cloudflare Python Worker 加上一個 Vectorize index，部署在 Workers Free 方案。
設計理由見 [ADR-005](../docs/decisions/005-cloudflare-serverless.md)。

- **協定：** MCP 2026-07-28 無狀態（`server/discover`、`tools/list`、`tools/call`，並檢查標頭），另支援舊版無狀態 `initialize`。
- **工具：** `search_esg_reports(query, company?, top_k≤5, strategy="vector")`，輸出格式與 v1 相同，另附 `structuredContent`。
- **端點：** `POST https://<worker>.<subdomain>.workers.dev/mcp/<MCP_PATH_TOKEN>`；其他路徑一律回 404。
- **限制：** query 最多 500 字、body 最多 16 KiB、top_k 最多 5，company 只接受 50 家的實際名稱。

## 部署

需要 Cloudflare 帳號（Free 方案即可）與 OpenAI API key。

pywrangler 需要 uv 0.13.4 以上，舊版系統 uv 可以改用 `uv tool run --from "uv>=0.13.4" uv ...`。

### 1. 建立 Vectorize index（只做一次）

先建 metadata index，再灌資料：

```bash
npx wrangler vectorize create esg-reports-256 --dimensions=256 --metric=cosine
npx wrangler vectorize create-metadata-index esg-reports-256 --property-name=company --type=string
```

### 2. 匯出並灌入向量

資料來自 esg-rag-query-system 的 `db-backup-v1` release，不放進 repo：

```bash
gh release download db-backup-v1 --repo WilliamCHIU-ETH/esg-rag-query-system
mkdir -p data && tar -xzf esg_50_vector_db.tar.gz -C data/
python scripts/export_to_vectorize.py data/esg_50_vector_db data/esg256.ndjson data/full1536.npz
npx wrangler vectorize insert esg-reports-256 --file data/esg256.ndjson --batch-size 1000
```

`export_to_vectorize.py` 不依賴 chromadb，直接讀 sqlite 與 HNSW 檔，因為備份的 schema 用 chromadb 0.4.15 和 0.6.3 都打不開。只需要 `numpy`。

### 3. 設定 secrets 並部署

```bash
cd worker
uv sync
npx wrangler secret put OPENAI_API_KEY
python -c "import secrets; print(secrets.token_urlsafe(24))" > .env.mcp-token
tr -d '\n' < .env.mcp-token | npx wrangler secret put MCP_PATH_TOKEN
uv run pywrangler deploy
```

- `OPENAI_API_KEY`：建議用專用 project 的 restricted key（只允許 embeddings），帳戶關閉自動儲值。
- `MCP_PATH_TOKEN`：存在本機的 `.env.mcp-token`（已被 gitignore），等同密碼，不要分享或截圖。
- 換 token：重新執行 `secret put`，再到 Claude 更新 connector 網址。

## 加進 Claude

1. 取得完整網址：

   ```bash
   echo "https://esg-mcp.<subdomain>.workers.dev/mcp/$(cat .env.mcp-token)"
   ```

2. 在 Claude 設定 → Connectors → Add custom connector，名稱填 ESG，URL 填上面的網址，驗證留空。
3. 在對話裡啟用後，問「台積電的範疇三排放怎麼揭露？」試試看。

## 測試

測試在 CPython 下 stub 掉 `workers`、`js`、`pyodide.ffi`，並用假的 OpenAI 與 Vectorize，不會連網路：

```bash
cd worker
python -m pytest tests -q
```

測試涵蓋：
- 路徑 token 不符回 404，且不呼叫 OpenAI
- body 超過上限回 413
- JSON-RPC 錯誤碼
- 2026-07-28 標頭檢查
- 舊版 `initialize`
- 參數驗證：query 500 字、top_k、strategy、company 白名單
- 上游錯誤不帶內部細節
- 正常 `tools/call` 的輸出格式與 Vectorize 查詢參數

## 實測數字（Workers Free，2026-10-28，`wrangler tail`）

| 方法 | n | CPU 中位數 / 最大（ms） | wall 中位數 / 最大（ms） |
|---|---|---|---|
| `tools/call`（OpenAI + Vectorize） | 20 | 59.5 / 141 | 488 / 727 |
| `server/discover` | 10 | 14.5 / 38 | 15.5 / 39 |
| `tools/list` | 10 | 17.5 / 51 | 18 / 53 |

40 次全部成功，沒有 1102。CPU 超過 Free 名目的 10 ms，但這次實測沒被擋，見 ADR-005 Known Limitations。

bundle：上傳 119 KiB / gzip 約 35 KiB。
