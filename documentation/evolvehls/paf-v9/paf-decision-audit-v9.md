# PAF Architecture Decision Audit

**Revision:** 9  
**Basis:** revision-8 decisions, prior soundness reviews, recent autonomous-EDA/program-evolution literature, and current framework capabilities.

## Summary verdict

- **Keep:** 12 revision-8 decisions.
- **Revise/clarify:** 10 revision-8 decisions.
- **Add:** 10 missing decisions.
- **Remove:** no core property, but several implementation assumptions are deferred or moved behind adapters.

## Decision-by-decision audit

| ID | Verdict | Weakness found | Revision-9 correction |
|---|---|---|---|
| DEC-001 Product identity | Keep, clarify | “Assurance layer” could remain vague. | Define the smallest complete product as kernel + control + assurance, with concrete invariants and outputs. |
| DEC-002 Three packages | Keep, rename | Package boundaries did not expose semantic/control/assurance responsibility clearly. | Use `paf.kernel`, `paf.control`, `paf.assurance`; internal modules are allowed but no early services. |
| DEC-003 Append-only ledger | Revise | Event sourcing, current state, concurrency, and bootstrap migration were underspecified. | Accepted events are authoritative; projections are rebuilt. Bootstrap remains atomic-file based; SQLite WAL begins in reusable core. Add optimistic revision checks and operation IDs. |
| DEC-004 One primary graph | Keep, clarify | “Primary graph” could still imply graph authority. | The ledger is authoritative; Semantic Work Graph is the primary planning projection. Other graph views are derived. |
| DEC-005 Universal loop | Revise | One loop could become an unbounded generic agent cycle. | Add deterministic gates, exact subject binding, independence policy, budgets, no-progress detection, graph-growth limits, and terminal states. |
| DEC-006 Capability execution | Revise | Capability discovery could be mistaken for trusted capability evidence. | Separate `CapabilityRequest` from `RouteBinding`; bind exact deployment, framework, tools, workspace, credentials, cost, data boundary, and evidence. No silent fallback. |
| DEC-007 EvaluationProtocol | Revise | Full experimental protocol is excessive for routine coding. | Introduce generic `AssessmentProtocol` with lightweight validation and full experiment profiles. Both remain immutable and versioned. |
| DEC-008 Evaluation firewall | Keep, stage | Enforcement level was not tied to implementation phases. | Bootstrap protects controller validation and exact-base evaluator assets; full read-only/hidden evaluator separation arrives before autonomous optimization. |
| DEC-009 SearchPolicy adapter | Keep, defer | Search abstractions were entering the roadmap before basic completion semantics. | Keep the adapter boundary; implement only after AssessmentProtocol and firewall are operational. |
| DEC-010 Candidate lineage optional | Keep | No major defect. | Keep candidate/archive records outside ordinary coding core. |
| DEC-011 Independent assessment | Strengthen | Independence lacked dimensions, exceptions, and exact-head requirements. | Add `IndependenceAssessment`; bind exact subject and record model/provider/session/context/workspace/prior involvement. |
| DEC-012 Four packages | Simplify | Four schema families risk duplication. | One `PackageManifest` envelope with Audit, Evidence, Reproduction, and Completion profiles. |
| DEC-013 Tiered mediation | Strengthen | Protected effects lacked freshness and commit-boundary semantics. | Add effect classes, EffectIntent, fresh AuthorizationWitness, commit-time revalidation, EffectReceipt, and reconciliation. |
| DEC-014 Standards reuse | Keep, qualify | MCP/A2A declarations could be treated as trust evidence. | Protocol metadata is untrusted input. PAF maps it to local descriptors, policy, and evidence. Standards are optional adapters. |
| DEC-015 Backend order | Revise | LangGraph was prioritized before proving a second agent runtime and local semantics. | Current Cline → stable local contracts → OpenHands adapter → LangGraph → Temporal when required. |
| DEC-016 Minimal persistence | Revise | Revision 8 implied immediate SQLite migration despite a file-based bootstrap. | Preserve atomic files for bootstrap. Introduce SQLite WAL only in reusable core with explicit migration and backup. |
| DEC-017 Immutable context | Strengthen | RAG, retrieval provenance, staleness, and untrusted-content handling were incomplete. | Add SourceSnapshot, IndexSnapshot, RetrievalRun, RetrievedSpan, ContextTransformation, deterministic-first retrieval, and context-release policy. |
| DEC-018 No hidden reasoning | Keep | No major defect. | Store concise rationale, alternatives, decisions, and evidence—not private chain-of-thought. |
| DEC-019 Recovery semantics | Keep, reorder | Prerequisite detection was scheduled after block/recovery work even though it caused current failures. | Bootstrap order becomes phase identity → structured validation → prerequisite preflight → block operations → partial recovery. |
| DEC-020 Domain profiles | Strengthen | Extension collision and schema ownership were not explicit. | Domain namespaces and registries cannot override kernel identities or protected invariants. |
| DEC-021 Policy cannot self-relax | Keep | Needed policy layering. | Separate immutable invariants, protected policy, methodology, mutable heuristics, and role guidance. |
| DEC-022 Delayed extraction | Revise | Earlier roadmap delayed extraction until too many domain features. | Extract after stable core API, local + second runtime conformance, recovery, package profiles, and one real EvolveHLS campaign. FIZZ is not a prerequisite. |

## New controlling decisions

### DEC-023 — Semantic model, encoding, and canonical bytes are separate

The semantic contract is independent of JSON. Revision 1 uses a restricted JSON encoding and a separately identified canonical byte profile. Numeric, Unicode, null/absent, unknown-field, set-order, duplicate-key, algorithm-agility, and self-digest rules are normative.

### DEC-024 — Schema evolution is explicit

Every contract declares schema identity/version and compatibility behavior. Unknown fields, unsupported versions, migrations, and source lineage are tested from the first slice. Silent coercion is forbidden.

### DEC-025 — Active run identity is controller state

Generation, task review, implementation, controller validation, exact-head review, and remediation each receive durable run and phase identity. Monitoring never infers “active” solely from the newest directory.

### DEC-026 — Protected effects require commit-time authorization

An earlier approval or policy result is insufficient if its base, dependencies, scope, or eligibility changed. The controller revalidates a witness bound to the exact effect immediately before durability.

### DEC-027 — External effects are idempotent or reconcilable

Every protected external operation declares an idempotency key, known retry conditions, receipt, and reconciliation procedure. Ambiguous success cannot be treated as ordinary failure and blindly retried.

### DEC-028 — Error and block taxonomies are normative

Errors record source, operation, retryability, safe-retry conditions, partial effects, evidence, owner, and required action. Block class determines allowed recovery operations.

### DEC-029 — Budgets are multidimensional but incremental

Bootstrap tracks tokens/cost, wall time, attempts, and tool timeout. Later profiles add compute, storage, egress, licenses, human-review time, and physical resources. Budget changes are explicit allocations, not hidden route side effects.

### DEC-030 — RAG is a context adapter, not memory authority

No retrieval framework is authoritative. Deterministic structural and lexical retrieval is implemented first. Dense/hybrid retrieval is adopted only after a task-grounded benchmark.

### DEC-031 — Conformance begins with every slice

Each contract slice carries valid, invalid, adversarial, canonical, migration, unknown-version, compatibility, and property-based tests as applicable. A late “conformance phase” only integrates the corpus.

### DEC-032 — Bootstrap and product semantics are explicitly separated

The bootstrap may use pragmatic file state, Git, Cline, and operator scripts. Every bootstrap-local record identifies its future PAF contract or remains clearly temporary. Bootstrap defects are repaired outside the product backlog when they prevent the backlog from executing.
