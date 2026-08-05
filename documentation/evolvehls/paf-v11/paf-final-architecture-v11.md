# PAF Architecture v11

**Status:** proposed authoritative baseline  
**Supersedes:** PAF v10  
**Date:** 2026-08-04

## 1. Purpose

PAF is a portable, evidence-backed progressive-refinement and campaign-control framework.

PAF turns an incomplete Intent into increasingly precise accepted models, derives an executable Work Graph, routes work through dynamically selected external agents and tools, and uses evidence and assessment to promote, repair, branch, supersede, or revise those models.

PAF is not itself a coding agent, workflow scheduler, EDA tool, hardware generator, optimizer, vector database, graph database, or experiment tracker. It integrates those capabilities through typed contracts and adapters.

## 2. Generic refinement stack

```text
Intent
  ↓
Problem Model
  ↓
Solution Model
  ↓
System Model
  ↓
Activity Model
  ↓
Work Graph
  ↓
Execution
  ↓
Evidence
  ↓
Assessment
  ↓
Revision or Promotion
```

“Architecture” remains a human/domain alias for a System Model. It is not the root PAF object.

### Intent

Defines the requested outcome, supplied artifacts, constraints, allowed effects, success definition, assessment profile, human gates, and budget. It remains close to the user’s language and must not silently add major engineering choices.

### Problem Model

Separates facts, source claims, interpretations, assumptions, unknowns, ambiguities, risks, questions, scope, and required evidence.

### Solution Model

Records the selected general strategy, alternatives, rejected alternatives, rationale, required capabilities, expected outcomes, and unresolved tradeoffs.

### System Model

Defines entities, relationships, capability contracts, interfaces, data contracts, invariants, policies, authority boundaries, external adapters, assessment contracts, compatibility rules, and migration rules.

### Activity Model

Defines phases or search stages, dependencies, refinement/exploration policy, evaluation protocols, fidelity ladder, budgets, stopping conditions, recovery policy, and promotion gates. A roadmap, experiment plan, or exploration plan is a projection of an Activity Model.

### Work Graph

Contains concrete Work Items with objectives, typed inputs and outputs, dependencies, required capabilities, context requirements, allowed effects, acceptance criteria, evidence requirements, assessment profile, recovery policy, and budget. The controller owns final Work Item identities.

## 3. One refinement protocol

Every transition uses:

```text
PROPOSE
→ deterministic validation
→ independent critique when required
→ REPAIR or ACCEPT
→ ASSESS
→ PROMOTE, REVISE, BRANCH, SUPERSEDE, or REJECT
```

The records are:

- `RefinementRequest`
- `RefinementProposal`
- `RefinementReview`
- `RefinementDecision`

A proposal can be promoted only when its source identity is current, deterministic checks pass, required critique is approved, unresolved issues are explicitly admissible, and all narrowing, expansion, assumptions, and decisions are traceable.

## 4. Common typed envelope

Every model has a common envelope and a typed payload:

```yaml
schema_version: 1
model_id: ...
model_kind: intent | problem | solution | system | activity | work-graph
revision_id: ...
parent_revision_refs: [...]
intent_ref: ...
status: proposed | accepted | superseded | rejected

purpose: ...
scope: ...
source_refs: [...]
decision_refs: [...]
policy_refs: [...]
capability_refs: [...]

assumptions: [...]
unknowns: [...]
constraints: [...]
non_goals: [...]
risks: [...]
required_evidence: [...]
assessment_ref: ...

created_by: ...
created_at: ...
base_revision: ...
content_digest: ...

payload: ...
```

PAF retains typed semantics; it does not collapse all records into an untyped knowledge object.

## 5. Authority and state

Authoritative semantic state consists of:

```text
append-only accepted semantic events
+ immutable content-addressed artifacts
```

Current models, Work Graph state, execution state, evidence graphs, and monitoring views are rebuildable projections.

Git remains a source and artifact identity mechanism, but it is not the complete semantic state model.

Authority precedence is explicit and profile-configurable. The default order is:

```text
approved protected decision
> accepted model revision
> accepted requirement or protocol
> authoritative source record
> supporting source
> derived summary
> model inference
```

Conflicts are represented, not silently resolved.

## 6. Capabilities and adapters

Work requests semantic capabilities rather than products, agent names, or shell commands.

A `CapabilityContract` defines:

- semantic operation;
- typed input/output schemas;
- preconditions and postconditions;
- invariants;
- effects and reversibility;
- idempotency;
- failure taxonomy;
- evidence requirements;
- authorization requirements;
- compatible adapter implementations.

The same capability may be exposed through Python, C++, CLI, MCP, a local process, an agent runtime, or a remote service.

Every adapter must support or explicitly reject:

- capability declaration;
- typed invocation;
- context input;
- event correlation;
- cancellation;
- timeout;
- health probing;
- partial-result preservation;
- effect receipts;
- normalized errors;
- workspace identity;
- artifact export;
- cost/resource reporting.

## 7. Dynamic routing

A Route may bind:

- model;
- agent runtime;
- tool adapters;
- workspace/sandbox;
- retrieval provider;
- workflow backend;
- compute resource;
- security/data policy;
- budget.

Route selection may consider compatibility, trust, access class, cost, latency, health, queue state, resources, historical performance, confidence, user preferences, and reproducibility pins.

Dynamic switching may change **how** work executes. It may not silently change:

- objective;
- accepted constraints;
- permissions;
- allowed effects;
- evaluator;
- acceptance criteria;
- assessment protocol;
- promotion policy.

Every route decision records candidates, inputs, selection rationale, fallback, and resulting route identity.

## 8. External-framework reuse

PAF must not rebuild existing execution infrastructure.

- Keep the current Cline bootstrap as stage-0 and first execution backend.
- Integrate OpenHands as an open-source coding backend after core contracts stabilize.
- Use LangGraph for adaptive cyclic refinement/recovery graphs when needed.
- Use Temporal for durable distributed activities and long-running campaigns when needed.
- Support other agent SDKs and multi-agent systems through optional adapters.
- Use existing search/evolution systems behind `SearchPolicy`.

PAF owns semantic refinement, identity, evidence, assessment, recovery, and promotion—not generic agent loops, workflow durability, or optimization algorithms.

## 9. Context and RAG

Authoritative objects and external artifacts are registered as typed Source Records.

Retrieval constructs immutable `ContextPackage` revisions through exact, structural, lexical, optional dense, and optional graph retrieval.

A ContextPackage records:

- exact selected spans;
- ordering;
- token budget;
- exclusions;
- query;
- retriever and reranker versions;
- index snapshot;
- authority/trust/freshness filtering;
- provenance.

RAG never becomes an authority store, and model memory never replaces persisted records.

## 10. Evidence and assessment

PAF distinguishes:

- `Artifact`
- `Observation`
- `Claim`
- `Criterion`
- `EvidenceItem`
- `AssessmentProtocol`
- `CriterionAssessment`
- `CompletionAssessment`
- `PromotionDecision`

Base profiles:

- validation for routine engineering;
- experiment for reproduction, optimization, exploration, and research.

An `AssessmentProtocol` fixes baseline and subject identities, toolchain epoch, benchmarks, evaluator, correctness constraints, metrics, seeds, repetitions, aggregation, uncertainty, fidelity ladder, timeout/failure semantics, generalization scope, cost accounting, promotion rules, and evaluator-integrity controls.

Candidate work cannot silently modify evaluator assets, baselines, benchmarks, parsers, seeds, or promotion rules.

Search retention, technical completion, promotability, and protected-transition authorization remain separate.

## 11. Recovery and nonlinearity

Failures are repaired at the layer where the defect exists:

```text
implementation defect       → remediate Work Item
invalid Work Item           → revise Work Graph
invalid sequencing/protocol → revise Activity Model
missing capability          → revise System Model or create CapabilityGap
invalid solution hypothesis → revise Solution Model
ambiguous understanding     → revise Problem Model
changed objective           → revise Intent
```

Supported operations include retry, continue, remediate, partial-work recovery, effect reconciliation, upstream revision, branching, supersession, rollback, and termination.

A `PartialWorkManifest` binds exact base, changes, artifacts, completed criteria, validation evidence, gaps, assumptions, effects, and compatibility requirements.

## 12. Profiles

### EvolveHLS

Target: synthesis-tool capabilities.

EvolveHLS evolves SODA-OPT and Bambu representations, passes, transformations, algorithms, APIs, scheduling, binding, memory, IR, verification, estimation, and backend integrations. It produces `ToolRevision` and `CapabilityContract` revisions with conformance, compatibility, migration, and QoR evidence.

It does not normally optimize applications by rewriting their C/C++ source.

### FIZZ

Target: accelerator/system designs and mappings.

FIZZ refines designs by composing and parameterizing exposed capabilities, including verified MLIR Transform schedules, SODA-OPT transformations and partitioning, dataflow composition, Bambu APIs/configurations, simulation, and physical evaluation.

It produces `DesignRevision`, `CandidateArchive`, lineage, QoR evidence, and scoped design assessment.

When a required refinement cannot be expressed, FIZZ emits a `CapabilityGap`, which may initiate an independent EvolveHLS campaign. Neither profile intrinsically depends on the other.

### Hardware generation

PAF can host specification-to-RTL, hierarchical RTL, verification, ASIC hardening, PCB/system design, and physical-design profiles through domain System Models, capabilities, validators, evaluators, and safety policies.

### Paper reproduction

A paper is an input source. Source claims, PAF interpretations, engineering decisions, implementation evidence, and conclusions remain separate.

## 13. Architecture-to-Work-Graph generation

```text
accepted Intent/Problem/Solution/System/Activity models
+ repository-state projection
+ task/evidence history
→ WorkGraphProposal
→ deterministic validation
→ independent critique
→ repair
→ accepted Work Graph revision
```

The repository-state projection includes implemented and partial capabilities, tests, open PRs, completed/blocked/superseded/active work, capability gaps, known defects, and adapter availability.

The planner proposes logical keys. The controller assigns authoritative IDs.

Validators enforce:

- unique controller-owned identities;
- acyclic dependencies;
- complete source/decision/requirement traceability;
- preservation of completed work;
- active-work immutability;
- bounded paths and effects;
- no silent scope expansion;
- no unsupported framework reinvention.

## 14. Minimal package structure

```text
paf.kernel
  identity, typed records, revisions, relations, semantic ledger

paf.refinement
  models, proposals, validation, critique, repair, promotion

paf.control
  Work Graph, capabilities, routing, execution, effects, budgets, recovery

paf.assurance
  protocols, evidence, assessment, packages, promotion

paf.context
  source registry, retrieval, Context Packages

paf.adapters
  Cline, local process, Git/GitHub, OpenHands, SODA-OPT, Bambu, others
```

These are package boundaries, not microservices.

## 15. Bootstrap self-hosting boundary

The existing bootstrap is stage-0 infrastructure.

It is trusted for:

- controller-owned identity;
- one-active-task sequencing;
- exact-base binding;
- authorization;
- bounded execution;
- production validation;
- checkpoint and draft-PR publication gates.

Models are not trusted for final identities, authority decisions, completion, or promotion.

Migration follows a strangler pattern:

```text
working bootstrap behavior
→ typed reusable PAF contract
→ reusable implementation under paf/
→ bootstrap wrapper calls reusable implementation
→ duplicate bootstrap logic removed after equivalence tests
```

The CLI remains compatible during migration.

## 16. Missing contracts to implement

1. Common model envelope and layer payload schemas.
2. RefinementRequest/Proposal/Review/Decision schemas.
3. Information-preservation and semantic-drift rules.
4. Source authority/conflict precedence.
5. CapabilityContract and adapter conformance suite.
6. Repository-state projection.
7. Work Graph mutation/reconciliation contract.
8. AssessmentProtocol and evaluator-firewall conformance.
9. Route-selection/switching audit contract.
10. ContextPackage and retrieval benchmark.
11. PartialWorkManifest and effect reconciliation.
12. Audit/Evidence/Reproduction/Completion package profiles.
13. EvolveHLS, FIZZ, hardware-generation, and reproduction profile schemas.

## 17. Simplicity rules

1. One typed model envelope.
2. One refinement lifecycle.
3. One append-only semantic ledger.
4. One Work Graph representation.
5. One capability abstraction.
6. One assessment framework with profiles.
7. External systems own agent loops, workflow durability, search algorithms, telemetry, and storage engines.
8. No subsystem without a demonstrated missing PAF invariant.
9. Start local and inspectable; distribute only when required.
10. Validate every abstraction in at least two substantially different profiles.

## 18. Novelty

PAF’s contribution is not autonomous coding, RTL generation, EDA orchestration, RAG, multi-agent roles, program evolution, or design-space search by itself.

PAF provides a portable semantic and assurance substrate for progressive, evidence-backed refinement from intent to executable work, preserving model lineage, capability and evaluator identity, dynamic route decisions, recovery, criterion-level assessment, and promotion scope across heterogeneous agents, workflows, EDA tools, and optimizers.
