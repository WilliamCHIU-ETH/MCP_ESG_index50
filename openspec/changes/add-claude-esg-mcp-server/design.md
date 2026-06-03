## Context

The source ESG RAG project already contains a local ChromaDB index configured by `CLAUDE_ESG_INDEX_PATH` with collection `esg_reports_50`, 17,144 chunks, 50 companies, and citation metadata. Complete ChromaDB assets are not shipped in this public repository, but a local machine can point the MCP server at a usable index.

The previous ablation result is useful as a design prior: under the existing corpus, ChromaDB index, and OpenAI `text-embedding-3-small` setup, vector-only retrieval outperformed adaptive hybrid retrieval on Context Precision and was competitive on Context Recall. The MCP implementation must not silently change this retrieval path and then claim the old result still applies.

The first user experience target is Claude Desktop or another Claude MCP client. Claude should call a retrieval tool, receive evidence chunks with citations, and synthesize the final answer itself. The MCP server should be an agent tool, not a Flask UI, not an ESG chatbot app, and not a new data product.

## Goals / Non-Goals

**Goals:**

- Provide a local stdio MCP server for Claude.
- Expose citation-ready ESG retrieval from the existing 50-company ChromaDB index.
- Use vector-only retrieval as the MVP default.
- Make retrieval behavior testable before implementation through TDD.
- Return bounded evidence so Claude receives useful context without flooding its context window.
- Fail fast when the query-time embedding path is missing, incompatible, or produces non-1536-dimensional vectors.

**Non-Goals:**

- Rebuild the 50-company PDF corpus, chunks, embeddings, or index in Phase 1.
- Migrate to Google embedding or PostgreSQL + pgvector in Phase 1.
- Build a hosted service, public API, auth, rate limiting, or UI.
- Support user-uploaded PDFs.
- Run a full RAGAS benchmark before the MCP prototype works.
- Have the backend LLM generate final answers in the MVP.

## Decisions

### Decision 1: Reuse ChromaDB for the MVP

Use the existing `data/esg_50_vector_db` as the MVP index.

Alternatives considered:
- Rebuild all PDFs/chunks/embeddings now: better reproducibility, but slower and unnecessary for validating Claude MCP value.
- Migrate to pgvector now: better future deployability, but adds Docker, SQL schema, and migration complexity before the MCP experience is proven.

Rationale: the core first risk is whether Claude can call the tool and use citation-ready evidence well. Rebuilding the corpus does not reduce that risk.

### Decision 2: Use explicit OpenAI query embeddings

The server must generate query embeddings with OpenAI `text-embedding-3-small` and pass them to ChromaDB via `query_embeddings`.

Alternatives considered:
- Use Chroma `query_texts`: unsafe because the local runtime can fall back to a default 384-dimensional embedding function, which is incompatible with the 1536-dimensional index.
- Attach a Chroma OpenAI embedding function: workable, but direct `query_embeddings` makes dimension validation explicit and easier to test.

Rationale: query-time embedding compatibility is the highest implementation risk.

### Decision 3: Keep one main tool first

Expose `search_esg_reports` as the only required MCP tool. Add `list_companies` only if implementation time permits after the main retrieval path is tested.

Alternatives considered:
- Multiple tools such as `get_company`, `cite_passage`, and `ask_esg`: more expressive, but increases tool-selection ambiguity for Claude.
- Backend answer generation: convenient for app-style use, but conflicts with the MCP positioning where Claude should synthesize from evidence.

Rationale: one well-described search tool is easiest for Claude to select and easiest to validate.

### Decision 4: Return evidence, not final answers

`search_esg_reports` returns ranked chunks with citation metadata. Claude writes the final answer.

Rationale: this keeps the MCP server focused on the durable asset: retrieval and citation. It also avoids duplicating Claude with a backend LLM.

### Decision 5: Test the contract before implementation

Implementation must start with failing tests for schema validation, query validation, embedding dimension validation, company filtering, top-k bounding, citation fields, and no backend LLM calls.

Rationale: the MCP value is in predictable tool behavior. TDD should protect the contract before runtime integration details are filled in.

## Risks / Trade-offs

- Query embedding dependency on OpenAI API -> Mitigation: isolate embedding behind an interface and use fake 1536-dimensional embeddings in unit tests.
- ChromaDB version and writable runtime behavior -> Mitigation: pin dependency expectations and test against a temporary copy of the DB for integration tests.
- Citation page mismatch or cross-page chunk ambiguity -> Mitigation: include page, source file, and chunk ID; validate manually in smoke tests.
- Claude may not call the tool if description is vague -> Mitigation: write a narrow tool description that names ESG reports, Taiwan companies, carbon targets, ESG policies, and sustainability indicators.
- Output may be too large for Claude -> Mitigation: enforce `top_k` bounds and per-chunk content limits.
- Old ablation may not transfer to MCP -> Mitigation: run a small vector-only vs current retrieval comparison after the MCP tool is working.

## Migration Plan

1. Implement and test the MCP server locally with the existing ChromaDB index.
2. Configure Claude Desktop to launch the stdio MCP server.
3. Run 20-30 manual Claude smoke-test questions and record failure cases.
4. Run a small retrieval comparison between vector-only and any alternate strategy before claiming MCP retrieval quality.
5. Only after the MCP path is validated, consider a separate change for Google embedding and pgvector migration.

Rollback is simple for the MVP: remove the Claude MCP config entry and stop using the local server. No source ESG index migration occurs in this change.

## Open Questions

No blocking open questions remain for the MVP. Google embedding, pgvector, hosted deployment, and complete benchmark reruns are explicitly deferred to later changes.
