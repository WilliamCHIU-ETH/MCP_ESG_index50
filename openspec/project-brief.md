# ESG RAG MCP Project Brief

## One-Sentence Positioning

A remote MCP server that lets any MCP client retrieve citation-ready evidence from the ESG reports of 50 Taiwan companies by URL, without users rebuilding the corpus, embeddings, or index. Achieved on 2026-10-28 (v2.0.0).

## Destination (True North)

**Reached (2026-10-28).** A remote MCP server on Cloudflare Workers (Free plan) with a
Cloudflare Vectorize index. Any MCP client can add the URL and query the ESG corpus — no local
setup, no local index, no local environment required. Phase 1's local stdio server validated
feasibility and remains the development mode. Decisions: ADR-004 (transport and auth) and
ADR-005 (Cloudflare Workers + Vectorize).

## Product Boundary

This project is an agent tool. It is not an ESG Q&A web app, not a data dashboard, and not a generic ESG data product.

The core asset is the calibrated retrieval pipeline and citation-ready evidence packaging. The value for users is saving the cost of collecting ESG reports, parsing PDFs, chunking text, embedding chunks, building indexes, tuning retrieval, and formatting citations.

## First Target User

Any MCP client (Claude Code, Claude, Cursor, etc.) connected by URL. The experience to optimize is:

1. User asks their AI tool an ESG question.
2. The AI tool calls the MCP retrieval tool.
3. The MCP server returns bounded evidence chunks with citations.
4. The AI tool writes the answer using those citations.

Local stdio was the Phase 1 delivery form and remains the development transport.

## Existing Assets

- Source ESG RAG project: external project, not included in this repo
- Source data: GitHub release `WilliamCHIU-ETH/esg-rag-query-system` `db-backup-v1` (ChromaDB backup, not committed)
- Remote index (v2): Cloudflare Vectorize `esg-reports-256` (256 dims, cosine, metadata index on `company`)
- Local ChromaDB index (v1): configure with `CLAUDE_ESG_INDEX_PATH`
- Collection: `esg_reports_50`
- Corpus: 50 Taiwan companies, 17,144 chunks
- Embedding: OpenAI `text-embedding-3-small`, 1536 dimensions (v1); truncated to 256 dimensions (v2)
- Metadata: `company`, `source_file`, `page`, `chunk_id`, `char_count`, `language`
- Evaluation evidence: prior ablation comparing vector-only, keyword-only, and adaptive hybrid retrieval

## Key Decisions (Phase 1, historical)

> Phase 1 decisions below are kept for history. Current decisions live in `docs/decisions/` (ADR-005 for v2).

### Phase 1 uses the existing ChromaDB index

Do not rebuild the 50-company PDF, chunk, embedding, and index pipeline in the first phase. The MCP experience can be validated faster by reusing the existing index.

### Phase 1 defaults to vector-only retrieval

Prior ablation showed vector-only performed best under the old corpus, OpenAI embedding, ChromaDB, and RAGAS setup. Treat this as a design prior. Do not claim the same quality after MCP-specific changes until a small re-validation is run.

### Phase 1 returns evidence, not final answers

The backend should not generate final ESG prose answers in the MVP. Claude is the agent and should synthesize the answer from returned evidence.

### Query embedding compatibility is a hard requirement

The existing index expects 1536-dimensional vectors. The server must generate query embeddings using a compatible path and should fail fast on dimension mismatch.

## Phase 1 Definition (historical, completed 2026-06-09)

Phase 1 succeeds when a local Claude MCP server can:

- expose `search_esg_reports`;
- accept a natural-language ESG query;
- optionally filter by company;
- search the existing 50-company ChromaDB index using vector-only retrieval;
- return bounded citation-ready chunks;
- let Claude produce a cited answer;
- pass automated unit tests and at least 20-30 manual Claude smoke-test questions.

## Phase 1 Non-Goals (historical)

- Google embedding migration
- PostgreSQL + pgvector migration
- hosted deployment
- public API
- UI
- authentication and rate limiting
- user-uploaded PDFs
- automatic corpus refresh
- full RAGAS rerun
- agent-agnostic optimization

## Phase 2 Focus

The remote deployment is decided in [ADR-005](../docs/decisions/005-cloudflare-serverless.md)
(Cloudflare Workers + Vectorize; the earlier pgvector + Gemini plan is superseded). Remaining
work items live in `openspec/backlog.md`. This brief does not track work items or decision
status; it only defines product positioning and scope.
