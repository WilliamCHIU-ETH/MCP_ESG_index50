# claude-esg-mcp-retrieval Specification

> **Status:** Closed — feasibility confirmed. Superseded by esg-platform-v2.
> **Closed date:** 2026-06-09

## Purpose
Phase 1 delivered an MCP server exposing `search_esg_reports` for Claude-callable vector retrieval over 50 Taiwan companies' ESG reports, using a local ChromaDB index and OpenAI `text-embedding-3-small`, with 18 unit tests passing and integration validated.
## Requirements
### Requirement: MCP server exposes ESG retrieval tool
The system SHALL expose a Claude-callable MCP tool named `search_esg_reports` for searching Taiwan ESG report evidence.

#### Scenario: Claude client lists the retrieval tool
- **WHEN** an MCP client requests available tools
- **THEN** the server returns `search_esg_reports` with a description that explains it searches Taiwan company ESG reports and returns citation-ready evidence

#### Scenario: Tool accepts minimal query input
- **WHEN** `search_esg_reports` is called with a non-empty `query`
- **THEN** the server accepts the request without requiring `company`, `year`, or `top_k`

### Requirement: Retrieval uses existing 50-company index
The system SHALL use the existing local ChromaDB collection `esg_reports_50` from the 50-company ESG index as the MVP retrieval source.

#### Scenario: Index is available
- **WHEN** the MCP server starts with a configured path to `data/esg_50_vector_db`
- **THEN** the server loads collection `esg_reports_50`

#### Scenario: Index is missing
- **WHEN** the configured index path does not exist or the collection cannot be loaded
- **THEN** the server fails with a clear startup or tool error that names the missing index problem

### Requirement: Query embedding is dimension-compatible
The system SHALL generate query embeddings compatible with the existing 1536-dimensional OpenAI `text-embedding-3-small` ChromaDB index.

#### Scenario: Embedding dimension is valid
- **WHEN** the embedding provider returns a 1536-dimensional query vector
- **THEN** the server queries ChromaDB using `query_embeddings`

#### Scenario: Embedding dimension is invalid
- **WHEN** the embedding provider returns a vector whose dimension is not 1536
- **THEN** the server rejects the retrieval request before querying ChromaDB and reports the dimension mismatch

### Requirement: Default retrieval strategy is vector-only
The system SHALL use vector-only retrieval as the default MVP strategy.

#### Scenario: Strategy omitted
- **WHEN** `search_esg_reports` is called without `strategy`
- **THEN** the server performs vector-only retrieval

#### Scenario: Unsupported strategy requested
- **WHEN** `search_esg_reports` is called with an unsupported `strategy`
- **THEN** the server rejects the request with a validation error naming the supported strategy values

### Requirement: Company filter limits retrieval scope
The system SHALL support an optional `company` input that limits results to matching company metadata.

#### Scenario: Company provided
- **WHEN** `search_esg_reports` is called with `company` set to `台積電`
- **THEN** returned results only include chunks whose metadata company is `台積電`

#### Scenario: Company omitted
- **WHEN** `search_esg_reports` is called without `company`
- **THEN** returned results may include chunks from any indexed company

### Requirement: Results are bounded and citation-ready
The system SHALL return a bounded list of evidence chunks with citation metadata suitable for Claude to cite.

#### Scenario: Search returns results
- **WHEN** retrieval finds matching chunks
- **THEN** each result includes `company`, `source_file`, `page`, `chunk_id`, `content`, `score`, and `citation`

#### Scenario: top_k exceeds limit
- **WHEN** `top_k` is greater than the maximum supported value
- **THEN** the server caps the number of returned results at the maximum supported value

#### Scenario: Content is too long
- **WHEN** a retrieved chunk exceeds the configured content length limit
- **THEN** the server returns bounded `content` while preserving citation metadata

### Requirement: Backend does not generate final answers
The MCP server SHALL return retrieved evidence and SHALL NOT call a backend LLM to generate final ESG answers in the MVP.

#### Scenario: Search called
- **WHEN** `search_esg_reports` is called
- **THEN** the server returns evidence chunks and metadata rather than a final prose answer

