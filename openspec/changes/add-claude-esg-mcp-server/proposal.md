## Why

This project should become a Claude-first MCP server so Claude can retrieve Taiwan ESG report evidence directly, without users downloading reports, creating embeddings, building indexes, or tuning retrieval. The valuable asset is the calibrated ESG retrieval workflow and citation-ready corpus, not a standalone ESG chatbot UI or a generic data product.

## What Changes

- Add a local Claude MCP server that exposes ESG report retrieval as agent-callable tools.
- Reuse the existing 50-company ChromaDB corpus as the MVP data source instead of rebuilding PDF, chunk, embedding, and index assets.
- Make vector-only retrieval the MVP default because prior ablation evidence showed it outperformed hybrid retrieval under the existing corpus, embedding, and evaluation setup.
- Return bounded, citation-ready evidence chunks with company, source file, page, chunk ID, score, and content.
- Add tests before implementation for tool contracts, retrieval boundaries, embedding dimension handling, citation fields, company filtering, and output limits.
- Defer Google embedding, PostgreSQL + pgvector migration, hosted deployment, user-uploaded PDFs, UI, authentication, rate limiting, automatic corpus updates, and full RAGAS reruns.

## Capabilities

### New Capabilities

- `claude-esg-mcp-retrieval`: Claude-callable MCP tools for searching ESG report evidence and returning citation-ready chunks from the existing 50-company index.

### Modified Capabilities

- None.

## Impact

- Adds MCP server code and tests in this workspace.
- Reads the existing ESG RAG project data from the local path configured by `CLAUDE_ESG_INDEX_PATH`.
- Requires a query-time embedding path compatible with the existing 1536-dimensional OpenAI `text-embedding-3-small` index.
- Requires Claude Desktop or another MCP client for end-to-end manual validation.
- May add Python MCP SDK and related test dependencies.
