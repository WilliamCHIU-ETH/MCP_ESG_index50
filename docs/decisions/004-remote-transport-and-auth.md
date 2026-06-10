# ADR-004: Remote Transport and Auth Model

**Date:** 2026-06-10
**Status:** Proposed

## Context

專案 true north 為公開代管的多使用者遠端 MCP server：使用者貼一個 URL 到
Claude Desktop 即可查詢 ESG 語料庫，無需本地設置。這需要兩個 Phase 1 從未
面對的決策：遠端 transport 協定，以及公開端點的認證與濫用防護模型。

Transport 現況（2026-06 查證）：MCP 規範自 2025-03-26 版起以 **Streamable HTTP**
（單一 `/mcp` endpoint，支援 POST/GET）取代 HTTP+SSE；舊的 HTTP+SSE 雙端點
模式已棄用，主要遠端 MCP 服務商的 SSE 相容期限於 2026 年陸續到期。
新建的公開伺服器不應以 SSE 為主要目標。

## Decision (Proposed)

### Transport

採用 **Streamable HTTP** 作為遠端 transport；stdio 保留作本地開發 transport。
兩者為同一 Retrieval layer 之上的平行 adapter（見 ADR-003 Remote Transport
Addendum）。不提供 HTTP+SSE 向下相容端點，除非實測發現主流 MCP client 仍需要。

### Auth（待定，本 ADR Accept 前必須選定）

候選方案：

1. **無認證 + IP rate limit** — 上手成本最低，符合「貼 URL 即用」；
   但無法識別濫用者、無法做 per-user 配額，公開語料庫可被無限爬取。
2. **API key（自助發放）** — 實作簡單、可 per-key 限流；
   但「貼 URL 即用」變成「先註冊拿 key」，增加使用摩擦。
3. **OAuth（MCP 規範的授權框架）** — 與 MCP spec 的 authorization flow 對齊、
   Claude Desktop 原生支援、長期最正確；但實作成本最高。

傾向：以方案 1（無認證 + rate limit）作為 public beta 起點，將方案 3 列為
正式版目標——語料庫為公開 ESG 報告書，資料本身無機密性，初期風險主要是
成本濫用而非資料外洩，rate limit 足以覆蓋。

## Acceptance Criteria

本 ADR 升級為 Accepted 前，必須：

1. 選定 auth 方案並記錄理由（含成本估算：embedding API 呼叫為主要邊際成本）。
2. 確認 rate limiting 策略（per-IP 或 per-key、限額數字、超限行為）。
3. 確認部署目標支援 Streamable HTTP 長連線（serverless 平台需驗證）。

## Consequences

- `host-mcp-service` backlog 項目以本 ADR 為進入條件之一。
- MCP server 需要第二個進入點（HTTP）；依 ADR-003，retrieval 邏輯不受影響。
- 公開端點引入維運成本（監控、限流、濫用處理），需在部署前納入成本模型。

## References

- [MCP Transports specification (2025-03-26)](https://modelcontextprotocol.io/specification/2025-03-26/basic/transports)
- [Why MCP's move away from SSE simplifies security (Auth0)](https://auth0.com/blog/mcp-streamable-http/)
- 相關決策：[ADR-003](003-mcp-as-adapter.md)（thin adapter 與 stateless 約束）
