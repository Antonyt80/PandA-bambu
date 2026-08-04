# PAF Final Architecture

**Revision:** 9  
**Status:** proposed final development baseline  
**Date:** 2026-08-04

## 1. Definition

PAF is a **portable engineering-campaign assurance and control layer**.

It converts intent into revisioned, dynamically adaptable work; delegates execution to existing agent, workflow, search, and tool systems; and preserves the identities, evidence, recovery state, and decisions required to assess, reproduce, and promote engineering results.

PAF is not an agent chat framework, coding agent, workflow engine, vector database, evolutionary optimizer, sandbox, telemetry backend, policy language, or EDA flow manager.

## 2. Smallest complete PAF

PAF is complete only when three concerns work together.

### `paf.kernel`

Owns semantic identity and accepted state:

```text
Campaign
ObjectRef / RevisionRef
IntentRevision
Requirement
Criterion
Decision
Proposal
WorkItemRevision
Relation
ContextPackageRef
ArtifactRef
ObservationRef
LedgerEvent
```

Responsibilities:

- logical and immutable revision identity;
- canonical encoding and typed digests;
- append-only accepted-event ledger;
- optimistic revision checks;
- proposal and decision state transitions;
- graph projections from typed relations.

### `paf.control`

Owns execution and recovery contracts:

```text
ExecutionContract
CapabilityRequest
RouteBinding
RoleContract
Attempt
Activity
ToolInvocation
EffectIntent
AuthorizationWitness
EffectReceipt
Checkpoint
PartialWorkManifest
BlockRecord
RemediationPlan
BudgetState
```

Responsibilities:

- compile accepted work into portable execution requests;
- select and bind agent, model, tool, workspace, and resource adapters;
- supervise bounded attempts;
- record protected effects;
- classify blocks and invoke explicit recovery operations.

### `paf.assurance`

Owns verification and completion:

```text
AssessmentProtocol
ValidationActivity
EvaluationRun
EvidenceLink
CriterionAssessment
IndependenceAssessment
CompletionAssessment
PromotionDecision
PackageManifest
```

Responsibilities:

- bind validation and experiments to exact subjects and protocols;
- protect evaluator identity;
- determine criterion status independently of producer self-report;
- generate Audit, Evidence, Reproduction, and Completion package profiles.

### `paf.domain.*`

Domain profiles add artifact types, tool adapters, metrics, methodology, and specialized criteria. They cannot redefine kernel identity, protected-effect authorization, ledger semantics, or completion rules.

The first domain profile is `paf.domain.evolvehls`.

## 3. Authoritative state

PAF has one authoritative semantic ledger and immutable artifact store.

```text
accepted command or external receipt
→ validated LedgerEvent
→ append-only transaction
→ rebuilt projections
```

Derived projections include:

- refinement view;
- Semantic Work Graph;
- execution/attempt view;
- evidence view;
- lineage view;
- operator status view.

The Work Graph is not an independent authority. It is a materialized view of accepted WorkItem revisions and dependency relations.

Bootstrap may continue using atomic JSON/JSONL files. The reusable core introduces SQLite WAL plus content-addressed files. This avoids a premature persistence rewrite while preserving a migration path.

## 4. Core invariants

1. **Controller-owned identity**  
   Models may propose descriptive content but never choose authoritative campaign, task, base, dependency, protocol, or protected-policy identity.

2. **Exact-subject binding**  
   Reviews, validations, decisions, and approvals bind to immutable digests and exact repository revisions.

3. **Proposals are not state**  
   Model output changes PAF state only after deterministic validation and required critique or approval.

4. **Append-only accepted history**  
   Corrections create new revisions or supersession events; they do not rewrite accepted history.

5. **Production-path evidence**  
   Completion cannot be inferred from direct shell success or model self-report when the production controller path is part of the criterion.

6. **No silent fallback**  
   Model, provider, framework, tool, context, permission, evaluator, and fidelity changes are recorded as RouteBinding or protocol revisions.

7. **Commit-time authorization**  
   A protected durable effect is reauthorized immediately before execution using a fresh witness bound to the exact effect.

8. **Evaluator integrity**  
   Candidate work cannot modify or silently influence its evaluator, baseline, benchmark, parser, or promotion policy.

9. **Context provenance**  
   Every agent attempt references the exact ContextPackage supplied to it.

10. **Bounded autonomy**  
    Every adaptive loop has budget, no-progress, graph-growth, and terminal conditions.

11. **Rebuildable views**  
    Monitoring, dashboards, RAG indexes, and summaries are projections, not substitutes for the ledger and artifacts.

12. **Protected policy cannot self-relax**  
    Search heuristics may evolve; safety, evaluator integrity, correctness, and approval boundaries may not be weakened by the same autonomous loop.

## 5. Universal control protocol

All adaptive PAF behavior follows one semantic protocol:

```text
PROPOSE
→ validate structure, scope, authority, and prerequisites
→ CRITIQUE when required
→ ACCEPT or REJECT
→ EXECUTE accepted work
→ ASSESS exact outcomes
→ COMPLETE, REPAIR, REPLAN, or TERMINATE
```

The subject may be a requirement, task contract, graph mutation, route, implementation, experiment, retrieval request, policy heuristic, or promotion decision.

The protocol is bounded by:

- maximum revisions and attempts;
- cost, time, token, and resource budgets;
- duplicate/no-progress detection;
- graph-growth limits;
- escalation and stop conditions.

Named agents are replaceable role bindings. A `RoleContract` specifies capabilities, context view, tools, write scope, output schema, assurance level, and independence requirements.

## 6. Work semantics

### WorkItem state

```text
PROPOSED
→ ACCEPTED
→ READY
→ RUNNING
→ BLOCKED | COMPLETED | CANCELED | SUPERSEDED
```

A blocked item is not retried generically. It receives a `BlockRecord` and an allowed recovery operation.

### Graph mutation

A Work Graph mutation contains:

- exact source graph revision;
- source trigger and rationale;
- added, revised, split, merged, or superseded items;
- dependency changes;
- duplication and coverage analysis;
- cost/risk estimates;
- acceptance and validation requirements;
- mutation limits and expiry.

Accepted mutations create a new graph revision. In-flight work is explicitly retained, canceled, or superseded.

## 7. Execution and adaptation

An `ExecutionContract` describes engineering needs without naming a product:

```text
required capabilities
input and output schemas
ContextPackage
allowed tools and effects
workspace and data labels
budget and deadline
validation obligations
checkpoint and cancellation semantics
```

A `RouteBinding` records the selected:

- model artifact and deployment;
- provider/account/funding source;
- agent framework/runtime;
- tool set and versions;
- workspace/sandbox;
- credentials and data boundary;
- resource allocation;
- expected cost and assurance level.

Route capability claims are evidence-bearing and versioned. Discovery metadata alone is not trust evidence.

Adaptation may replace or combine routes, add tools, revise context, escalate fidelity, or change search strategy. It may not silently change the task objective, evaluator, protected permissions, or data-egress policy.

## 8. Tools and protected effects

Tool execution is typed and extensible by executable/operation schema.

### Integration levels

- **L1 Observed:** framework executes tools; PAF records available events and constrains the environment.
- **L2 Delegated:** selected tools execute through PAF adapters.
- **L3 Mediated:** protected tools and durable effects execute only through PAF.

### Effect classes

```text
READ_ONLY
LOCAL_REVERSIBLE
LOCAL_DESTRUCTIVE
REMOTE_REVERSIBLE
REMOTE_IRREVERSIBLE
PUBLICATION
FINANCIAL_OR_RESOURCE_COMMITMENT
PHYSICAL_OR_FABRICATION
```

Protected effects use:

```text
EffectIntent
→ policy decision
→ AuthorizationWitness
→ freshness and binding check at commit
→ execution
→ EffectReceipt
→ reconciliation if outcome is ambiguous
```

MCP may transport tool metadata and calls, but MCP server claims and retrieved content are untrusted until mapped to PAF descriptors, policy, and evidence.

## 9. Assessment and evaluator integrity

`AssessmentProtocol` is the common abstraction.

### Validation profile

For ordinary coding tasks:

- exact commands and typed authorization rules;
- expected exit/result semantics;
- positive, negative, adversarial, migration, and compatibility tests;
- required production path;
- evidence capture.

### Experiment profile

For research and optimization:

- baseline and benchmark identities;
- Toolchain Epoch and environment;
- hard constraints;
- primary, secondary, diagnostic, and resource metrics;
- seeds, repetitions, aggregation, and uncertainty;
- fidelity ladder;
- holdout/generalization partitions;
- promotion rules and cost accounting.

Changing an assessment protocol creates a new revision. Results from incompatible revisions are not directly comparable without an explicit bridge assessment.

### Evaluation firewall

```text
candidate workspace       writable
protocol and evaluator    immutable/read-only
baseline                  immutable
benchmarks                 read-only or hidden
parser                     independently controlled
result ledger              append-only
promotion assessment       independent when required
```

## 10. Evidence, independence, and packages

A producer result is a claim, not automatic completion.

A `CriterionAssessment` records:

- exact criterion revision;
- status: satisfied, unsatisfied, waived, unknown, or not-applicable;
- evidence links;
- protocol revision;
- assessor identity and independence;
- limitations and confidence.

An `IndependenceAssessment` considers model, provider, session, prompt/context, workspace, prior involvement, tool access, organizational conflict, and exceptions. Diversity and independence are recorded separately.

PAF uses one generic `PackageManifest` with four profiles:

- **Audit:** reconstruct history and decisions;
- **Evidence:** support a criterion or claim;
- **Reproduction:** rerun exact work;
- **Completion:** decide readiness for a transition.

This avoids four parallel schema families while preserving four distinct outputs.

## 11. Recovery and failure semantics

### Block classes

```text
INFRASTRUCTURE
PROVIDER
TOOL
VALIDATION
IMPLEMENTATION_GAP
TASK_CONTRACT_DEFECT
MISSING_PREREQUISITE
STALE_BASE
CAPABILITY_MISMATCH
BUDGET
POLICY
SECURITY
CHECKPOINT_INCOMPATIBLE
AMBIGUOUS_EXTERNAL_EFFECT
CONTROLLER_FAILURE
```

### Recovery operations

```text
RETRY_TRANSIENT
CONTINUE_ATTEMPT
REMEDIATE_IMPLEMENTATION
REVISE_TASK
RESOLVE_PREREQUISITE
REGENERATE_FROM_BASE
RECOVER_PARTIAL_WORK
RECONCILE_EFFECT
REPLAN_GRAPH
TERMINATE
```

A `PartialWorkManifest` records exact base, tracked and untracked changes, completed criteria, validations, gaps, assumptions, external effects, and compatibility requirements.

Local bootstrap recovery may use Git patches and archived untracked files. Reusable PAF later represents the same information through typed artifacts and checkpoints.

## 12. Context, retrieval, and RAG

RAG is a replaceable context-construction subsystem, not PAF memory or authority.

Minimum records:

```text
SourceSnapshot
IndexSnapshot
RetrievalRequest
RetrievedSpan
RetrievalRun
ContextPackage
ContextTransformation
```

Retrieval order is deterministic-first:

```text
exact object/path/symbol
→ structural relation lookup
→ lexical/full-text retrieval
→ optional dense retrieval
→ fusion/reranking
→ policy and staleness filtering
→ immutable ContextPackage
```

Every retrieved span records source revision, digest, location, retriever/index version, query, score, rank, access label, and staleness.

Bootstrap stack:

- Git and content digests;
- ripgrep;
- tree-sitter/LSP/compiler indexes when available;
- SQLite FTS5;
- exact ledger and evidence references.

No RAG framework is mandatory. Haystack, LlamaIndex, PostgreSQL/pgvector, or Qdrant may be added behind `RetrieverProvider` after a PAF-specific retrieval benchmark demonstrates value.

Retrieved repository, paper, issue, MCP, and web content is treated as untrusted data, not executable instruction.

## 13. Security model

Minimum security records:

```text
PrincipalRef
CredentialRef
DataLabel
TrustZone
ToolDescriptor
PolicyInputSnapshot
PolicyDecision
AuthorizationWitness
RedactionRecord
```

Bootstrap requirements before autonomous coding:

- repository and write-path bounds;
- controller-owned publication;
- no secret values in prompts, logs, or artifacts;
- structured shell-free protected validation;
- network and package-install policy;
- exact base and branch binding;
- untrusted-content labeling;
- immutable evaluator assets;
- fail-closed policy for protected effects;
- forensic retention of failed attempts.

OPA is optional when policy volume or independent policy ownership justifies it. Typed local policy remains acceptable during bootstrap.

## 14. Persistence and distributed boundary

### Bootstrap

Atomic files, JSONL logs, Git objects, and content-addressed recovery archives remain acceptable.

### Reusable local core

SQLite WAL plus content-addressed blobs provides transactional append, projections, migration, backup, and inspectability.

### Distributed campaigns

Temporal or another durable engine is introduced only when real campaigns require process/host recovery, asynchronous waits, distributed workers, or multi-hour tool execution.

Before distributed operation, PAF must define idempotency keys, leases, fencing, optimistic concurrency, late-result rejection, delivery assumptions, clock handling, controller failover, queue durability, and reconciliation. These are not bootstrap prerequisites beyond stable IDs and operation keys.

## 15. Framework reuse

PAF deliberately reuses:

- Cline for the current bootstrap coding runtime;
- OpenHands as the first materially different coding-agent adapter;
- LangGraph for adaptive hierarchical execution after local semantics stabilize;
- Temporal for durable distributed campaigns when required;
- MCP for tool interoperability, under PAF security and authorization;
- A2A for delegation to remote opaque agents, when needed;
- OpenTelemetry for operational traces, logs, and metrics;
- OPA for complex externalized policy;
- in-toto/SLSA-compatible envelopes for released attestations;
- MLflow/DVC for experiment views when useful;
- Optuna, Ray Tune, OpenEvolve, CodeEvolve, or equivalent through SearchPolicy adapters;
- Haystack/LlamaIndex/pgvector/Qdrant through retrieval adapters.

PAF audit evidence remains authoritative even when an external framework offers tracing or state persistence.

## 16. Evolution and autonomous research

Evolutionary coding is an optional campaign profile, not a core runtime.

It adds candidate identity, mutation lineage, archive state, SearchPolicy, selection, plateau detection, and promotion scope while reusing the same assessment firewall and evidence model.

PAF distinguishes:

- current search candidate;
- best-known candidate set;
- design-specific specialization;
- reusable engineering improvement;
- research insight;
- promoted repository result.

## 17. EvolveHLS profile

`paf.domain.evolvehls` owns:

- Bambu, SODA-OPT, Verilator, VTR, OpenROAD, and scheduler/HPC adapters;
- compiler/IR/RTL/physical artifact types;
- Toolchain Epoch;
- semantic-equivalence and correctness profiles;
- timing, area, power, performance, and compile-time metrics;
- progressive fidelity;
- paper/specification claims and adaptation hypotheses;
- benchmark and contamination governance.

Canonical campaign:

```text
paper or research objective
→ source-bound interpretation
→ explicit assumptions and decisions
→ Work Graph
→ implementation
→ correctness and regression validation
→ controlled QoR experiments
→ repair or additional experiments
→ scoped conclusion
→ Audit/Evidence/Reproduction/Completion packages
```

A negative or conditional result is valid completion when the methodology and conclusion are sound.

## 18. Implementation sequence

1. Repair and verify the bootstrap overlay.
2. Complete BS-010 identity and canonicalization.
3. Internalize phase identity, validation, prerequisites, block semantics, and partial recovery.
4. Implement the minimal kernel contracts and event/error envelope.
5. Instrument the existing bootstrap as a shadow runtime.
6. Add durable local state and recovery.
7. Implement secure runtime and Cline adapter.
8. Add capability routing and budgets.
9. Implement criterion assessment and package profiles.
10. Add deterministic retrieval and immutable ContextPackages.
11. Implement dynamic Work Graph proposals and bounded replanning.
12. Run a bounded self-hosted campaign.
13. Add OpenHands and cross-runtime conformance.
14. Add LangGraph only after local mutation/recovery semantics are stable.
15. Add Temporal only after a real durability requirement.
16. Build EvolveHLS evaluation and evolution profiles.

## 19. Final novelty claim

PAF does not contribute another agent loop or evolutionary optimizer.

PAF contributes a portable engineering assurance and control substrate that keeps semantic work, exact context, heterogeneous execution, evaluator identity, recovery, evidence, and promotion scope coherent across different agent, workflow, retrieval, and search systems.
