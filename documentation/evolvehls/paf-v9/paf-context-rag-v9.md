# PAF Context and RAG Design

**Revision:** 9

## 1. Boundary

RAG constructs agent context. It does not define truth, durable memory, task authority, or completion.

The source artifact remains authoritative. Retrieved chunks and model summaries are derived views.

## 2. Contracts

```text
SourceSnapshot
  source identity, revision, digest, label, timestamp

IndexSnapshot
  source set, index implementation/version, configuration, digest

RetrievalRequest
  role, purpose, query, filters, budget, freshness, permitted labels

RetrievedSpan
  source revision, location, digest, method, score, rank, staleness

RetrievalRun
  request, index snapshots, candidates, fusion/reranking, exclusions

ContextPackage
  exact ordered selected material, token/size budget, transformations
```

Every attempt references a ContextPackage digest.

## 3. Retrieval cascade

1. exact object/revision and decision lookup;
2. exact file/path/symbol lookup;
3. build, call, registration, ownership, and provenance relations;
4. lexical/full-text retrieval;
5. optional dense retrieval;
6. fusion and reranking;
7. access, staleness, duplication, and token-budget filtering.

Exact and structural results are not displaced merely because a dense result has a higher opaque score.

## 4. Role-specific context

### Planner

Architecture decisions, objectives, repository overview, prior evidence, related implementations, literature claims, and open ambiguities.

### Implementer

Exact files/symbols, registrations, interfaces, tests, build rules, nearby implementations, task contract, and production validation path.

### Critic/assessor

Exact subject diff/head, criteria, decisions, evaluator, test evidence, prior findings, and independence requirements.

## 5. Dynamic retrieval

An agent may request more context through a typed RetrievalProposal. Policy validates scope and labels; retrieval produces a new ContextPackage revision; the attempt records the transition.

Silent direct access to an unrecorded vector store is nonconforming for protected work.

## 6. Initial implementation

Use native components first:

- Git object and revision lookup;
- ripgrep;
- tree-sitter, LSP, clang, MLIR, or project-native indexes where useful;
- SQLite FTS5;
- ledger/evidence queries;
- paper metadata and exact citation records.

No vector service is required for the first coding campaign.

## 7. Framework adapters

- Haystack is suitable for modular retriever/document-store pipelines.
- LlamaIndex is useful for specialized ingestion, AST splitting, routing, and property-graph experiments.
- PostgreSQL + pgvector is the preferred shared relational/vector deployment when scale and collaboration require it.
- Qdrant is optional for advanced dense+sparse fusion and reranking.

Selection follows a PAF retrieval benchmark rather than generic leaderboard claims.

## 8. Evaluation

Benchmark entries contain query, role, expected source spans/symbols/decisions, forbidden stale sources, and downstream task need.

Measure:

- required-source recall;
- rank quality;
- source-span precision;
- stale/forbidden source rate;
- redundancy and context size;
- latency and cost;
- downstream criterion success;
- unsupported-claim rate.
