# ESG RAG MCP Project Brief

## One-Sentence Positioning

Turn the existing Taiwan ESG RAG retrieval work into a Claude-first MCP server that lets Claude retrieve citation-ready ESG report evidence without users rebuilding the corpus, embeddings, or index.

## Product Boundary

This project is an agent tool. It is not an ESG Q&A web app, not a data dashboard, and not a generic ESG data product.

The core asset is the calibrated retrieval pipeline and citation-ready evidence packaging. The value for users is saving the cost of collecting ESG reports, parsing PDFs, chunking text, embedding chunks, building indexes, tuning retrieval, and formatting citations.

## First Target User

The first version is for Claude users, especially Claude Desktop or another Claude MCP client. The first experience to optimize is:

1. User asks Claude an ESG question.
2. Claude calls the MCP retrieval tool.
3. The MCP server returns bounded evidence chunks with citations.
4. Claude writes the answer using those citations.

Agent-agnostic support is a later expansion, not a Phase 1 constraint.

## Existing Assets

- Source ESG RAG project: external local project, not included in this repo
- Existing local ChromaDB index: configure with `CLAUDE_ESG_INDEX_PATH`
- Collection: `esg_reports_50`
- Corpus: 50 Taiwan companies, 17,144 chunks
- Embedding: OpenAI `text-embedding-3-small`, 1536 dimensions
- Metadata: `company`, `source_file`, `page`, `chunk_id`, `char_count`, `language`
- Evaluation evidence: prior ablation comparing vector-only, keyword-only, and adaptive hybrid retrieval

## Key Decisions

### Phase 1 uses the existing ChromaDB index

Do not rebuild the 50-company PDF, chunk, embedding, and index pipeline in the first phase. The MCP experience can be validated faster by reusing the existing index.

### Phase 1 defaults to vector-only retrieval

Prior ablation showed vector-only performed best under the old corpus, OpenAI embedding, ChromaDB, and RAGAS setup. Treat this as a design prior. Do not claim the same quality after MCP-specific changes until a small re-validation is run.

### Phase 1 returns evidence, not final answers

The backend should not generate final ESG prose answers in the MVP. Claude is the agent and should synthesize the answer from returned evidence.

### Query embedding compatibility is a hard requirement

The existing index expects 1536-dimensional vectors. The server must generate query embeddings using a compatible path and should fail fast on dimension mismatch.

## Phase 1 Definition

Phase 1 succeeds when a local Claude MCP server can:

- expose `search_esg_reports`;
- accept a natural-language ESG query;
- optionally filter by company;
- search the existing 50-company ChromaDB index using vector-only retrieval;
- return bounded citation-ready chunks;
- let Claude produce a cited answer;
- pass automated unit tests and at least 20-30 manual Claude smoke-test questions.

## Phase 1 Non-Goals

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

## Current Active Change

- `add-claude-esg-mcp-server`: **Complete** (Phase 1 MCP retrieval MVP delivered)

## Phase 2 Focus

Entry conditions before Phase 2 implementation begins:

- Canonical schema — 9 core entities defined (company, report, section, chunk, embedding, citation, query, result, evaluation)
- Three-layer separation — Ingestion / Retrieval / Consumer layers explicitly decoupled
- Startup mutation moved out of the query-serving path (ingestion job, not server startup)
- ADR-001: pgvector vs ChromaDB decision closed
- ADR-002: embedding model version governance policy defined

## Phase 2 Candidates

- Rebuild or migrate embeddings only if Phase 1 proves the MCP workflow is worth improving.
- Compare Google embedding against the existing OpenAI embedding path.
- Migrate storage from ChromaDB to PostgreSQL + pgvector if deployability or maintainability becomes the bottleneck.
- Add a corpus refresh pipeline for newer ESG reports.
- Run expanded retrieval and citation evaluation.
- Consider hosted MCP only after local Claude usage is validated.
