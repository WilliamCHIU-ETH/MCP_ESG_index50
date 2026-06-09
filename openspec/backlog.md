# ESG MCP Backlog

OpenSpec does not have a separate backlog command in this setup. Use active `openspec/changes/*` as executable backlog items, and use this file as the roadmap that decides which changes to create next.

## Backlog Policy

- Keep Phase 1 narrow until Claude can reliably use the local MCP tool.
- Create one OpenSpec change per coherent implementation slice.
- Do not mix corpus rebuild, storage migration, hosted deployment, and MCP tool contract work in the same change.
- Promote a backlog item into `openspec/changes/<name>/` only when it is ready for proposal/design/spec/tasks.

## Done

- `add-claude-esg-mcp-server`
  Phase 1 MVP. MCP server exposes `search_esg_reports`, vector retrieval via ChromaDB,
  18 unit tests pass, integration green. Closed 2026-06-09.

## Now

### `run-mcp-retrieval-validation`

Purpose: Validate whether MCP retrieval behavior preserves the old vector-only advantage.

Entry condition:
- Phase 1 MCP server can run locally.

Likely scope:
- 20-30 smoke-test questions.
- Small vector-only vs alternate retrieval comparison.
- Citation quality review.
- Failure taxonomy: tool selection, retrieval quality, citation format, context length.

## Next

### `document-claude-installation`

Purpose: Make the local Claude MCP setup repeatable.

Entry condition:
- MCP server entrypoint is stable.

Likely scope:
- Claude Desktop config example.
- Environment variables.
- Local index path expectations.
- Troubleshooting for missing API key, missing index, and embedding dimension mismatch.

## Later

### `compare-google-embedding-pipeline`

Purpose: Test whether Google embedding should replace or supplement the existing OpenAI embedding path.

Entry condition:
- Phase 1 MCP value is validated.

Likely scope:
- Confirm Google embedding endpoint and PDF input behavior.
- Test page-level or chunk-level embedding behavior.
- Compare embedding dimensions, cost, latency, and retrieval quality.
- Decide whether the whole corpus must be rebuilt.

### `migrate-index-to-pgvector`

Purpose: Move retrieval storage from local ChromaDB to PostgreSQL + pgvector if deployment or maintainability requires it.

Entry condition:
- There is a clear reason ChromaDB is blocking the next product step.

Likely scope:
- PostgreSQL schema for company, report, chunk, page, content, embedding, metadata.
- Vector search query implementation.
- Data migration from existing ChromaDB or regenerated chunks.
- Parity tests against the ChromaDB retrieval baseline.

### `rebuild-corpus-from-pdfs`

Purpose: Recreate the corpus from source PDFs when new years, new reports, or a new embedding strategy requires it.

Entry condition:
- Source PDF list and report year policy are defined.

Likely scope:
- Company/report manifest.
- PDF download or local import pipeline.
- Text extraction and chunking.
- Embedding generation.
- Index build.
- Corpus inventory report.

### `add-corpus-refresh-workflow`

Purpose: Support future updates of ESG reports without manual one-off rebuilds.

Entry condition:
- Rebuild pipeline exists and is reliable.

Likely scope:
- Report source manifest.
- Versioned corpus metadata.
- Incremental update strategy.
- Regression checks for retrieval and citation quality.

### `host-mcp-service`

Purpose: Evaluate hosted deployment after local Claude usage works.

Entry condition:
- Local MCP is useful and repeatable.

Likely scope:
- Deployment target.
- Auth and rate limiting.
- Data access model.
- Cost model.
- Operational monitoring.

## Explicitly Deferred

- UI or dashboard.
- Backend-generated ESG final answers.
- User-uploaded PDF ingestion.
- Full RAGAS benchmark before the MCP prototype is working.
- Agent-agnostic tool packaging before Claude-first usage is good.
