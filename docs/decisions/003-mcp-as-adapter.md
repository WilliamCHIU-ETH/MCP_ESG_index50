# ADR-003: MCP Server as a Thin Consumer Adapter

**Date:** 2026-06-09
**Status:** Proposed

## Context

Phase 1 MCP server 直接包含 retrieval 邏輯（embedding 呼叫、ChromaDB 查詢、結果格式化），導致傳輸層（MCP/stdio）與儲存層（ChromaDB）緊密耦合。任何儲存遷移或 retrieval 變更都需要修改 MCP server 本身。
本 ADR 尚待正式接受；待 RetrievalService 介面合約定義完成後（參見 esg-platform-v2/spec.md 的 Open Questions），狀態將更新為 Accepted。

2026-06-10 補充：專案 true north 確立為公開代管的多使用者遠端 MCP server
（Streamable HTTP，見 ADR-004）。adapter 層因此將存在**兩個** transport——
stdio（本地開發）與 Streamable HTTP（遠端正式）——共用同一個 Retrieval layer。
這使 thin adapter 從「可測試性投資」升級為遠端架構的必要條件。

## Decision

Phase 2 中，MCP server 僅作為薄 adapter。所有 retrieval 邏輯（embedding、向量搜尋、reranking、結果格式化）移至具備穩定 Python 介面的獨立 Retrieval layer。MCP tool handler 呼叫 Retrieval layer 並回傳其輸出。

## Consequences

**優點：** Retrieval layer 可獨立於 MCP 傳輸層進行測試。儲存遷移的影響範圍被隔離在 Retrieval layer 內。未來的其他 adapter（REST、gRPC）可重用相同的 layer。

**缺點：** 增加了一層抽象；檔案結構略微複雜。

## Interface Contract (to be defined)

```python
class RetrievalService:
    def search(self, query: str, company: str | None, top_k: int) -> list[EvidenceChunk]:
        ...
```

MCP handler 呼叫 `RetrievalService.search()` 並序列化回傳結果。MCP server 模組中不得有任何 ChromaDB 的 import。

## Remote Transport Addendum (2026-06-10)

在遠端多使用者模型（ADR-004）下，本 ADR 新增三條約束：

1. **Stateless** — `RetrievalService` 不得持有任何 per-session 或 per-user 狀態，
   所有呼叫必須並發安全。session 管理（若有）屬 transport adapter 層。
2. **職責邊界** — 認證與速率限制是 adapter 層（Consumer layer）的職責，
   不得滲入 `RetrievalService` 介面或實作。
3. **合約先行** — 介面合約（`typing.Protocol` + 輸入/輸出 DTO，含 company、
   source_file、page 等 citation metadata）的定義完成是本 ADR 升級為
   Accepted 的前提，而非事後補充。
