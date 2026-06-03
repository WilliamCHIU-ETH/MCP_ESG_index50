## 1. Test Foundation

- [x] 1.1 Add a minimal Python project/test structure for the MCP server without implementing retrieval behavior.
- [x] 1.2 Write failing tests for `search_esg_reports` input validation: non-empty query, supported strategy values, and `top_k` bounds.
- [x] 1.3 Write failing tests proving retrieval uses a 1536-dimensional query embedding and rejects any other dimension before querying ChromaDB.
- [x] 1.4 Write failing tests proving ChromaDB is called with `query_embeddings` and optional company metadata filtering.
- [x] 1.5 Write failing tests proving formatted results include `company`, `source_file`, `page`, `chunk_id`, `content`, `score`, and `citation`.
- [x] 1.6 Write a failing test proving the MVP returns evidence chunks and does not call a backend LLM to generate final answers.

## 2. Retrieval Core

- [x] 2.1 Implement configuration for index path, collection name, embedding model, maximum `top_k`, and maximum returned content length.
- [x] 2.2 Implement an embedding provider interface plus an OpenAI `text-embedding-3-small` provider.
- [x] 2.3 Implement a Chroma retrieval adapter that loads `esg_reports_50`, uses `query_embeddings`, and supports optional company filtering.
- [x] 2.4 Implement vector-only search as the default strategy and reject unsupported strategies.
- [x] 2.5 Implement citation-ready result formatting with bounded content and stable citation strings.
- [x] 2.6 Run the unit test suite and keep all tests passing after the retrieval core is complete.

## 3. MCP Server

- [x] 3.1 Add the Python MCP SDK dependency and a stdio server entrypoint.
- [x] 3.2 Register the `search_esg_reports` MCP tool with a Claude-oriented description and input schema.
- [x] 3.3 Connect the MCP tool handler to the tested retrieval core.
- [x] 3.4 Add MCP server startup error handling for missing index path, missing API key, and collection load failure.
- [x] 3.5 Add tests or command-level verification that the server lists `search_esg_reports` as an available MCP tool.

## 4. Integration Validation

- [x] 4.1 Add an integration test path that can run against a temporary copy of the local ChromaDB index when required environment variables are present.
- [ ] 4.2 Verify a real query such as `台積電的碳中和目標是什麼` returns bounded citation-ready evidence from the 50-company index.
- [x] 4.3 Document the Claude Desktop MCP config needed to launch the local stdio server.
- [ ] 4.4 Run 20-30 manual Claude smoke-test questions and record failures by category: tool selection, retrieval quality, citation format, or context length.
- [ ] 4.5 Run a small vector-only versus alternate retrieval comparison before making any MCP-specific retrieval quality claim.

## 5. Completion

- [x] 5.1 Run OpenSpec validation for `add-claude-esg-mcp-server`.
- [x] 5.2 Run the full available test suite.
- [x] 5.3 Summarize implemented behavior, test evidence, known limitations, and deferred Phase 2 items.
