# PAF Final Design Summary

**Revision:** 9  
**Role:** concise controlling summary; the detailed architecture and machine-readable decision set provide normative elaboration.

## Product

PAF is a **portable engineering-campaign assurance and control layer**.

It turns intent into revisioned work, delegates execution to existing agents/workflows/tools, and preserves the evidence and state required to assess, repair, reproduce, and promote engineering outcomes.

PAF is not an agent framework, workflow engine, optimizer, vector database, sandbox, telemetry service, or EDA flow manager.

## Three implementation areas

```text
paf.kernel
  identity, revisions, decisions, WorkItems, relations, accepted events

paf.control
  execution contracts, route bindings, activities, effects, budgets,
  blocks, checkpoints, remediation and recovery

paf.assurance
  assessment protocols, validation/evaluation, evidence, independence,
  completion, promotion and package manifests
```

Domain behavior is namespaced under `paf.domain.*`, initially `paf.domain.evolvehls`.

## Authoritative model

```text
append-only accepted semantic events
+ immutable/content-addressed artifacts
→ rebuildable Work, Evidence, Lineage, Execution and Status views
```

Bootstrap remains atomic JSON/JSONL/Git. SQLite WAL begins only in reusable core.

## Universal bounded loop

```text
PROPOSE
→ deterministic validation
→ independent critique when required
→ ACCEPT or REJECT
→ EXECUTE
→ ASSESS
→ COMPLETE, REPAIR, REPLAN or TERMINATE
```

The controller owns exact identity, base, dependencies, protocols, budgets and protected policy. Models propose bounded content and actions.

## Essential invariants

1. exact subject and base binding;
2. controller-owned authoritative identity;
3. no model output becomes state before validation;
4. accepted history is append-only;
5. completion requires production-path evidence;
6. route, tool, context, evaluator and fidelity changes are explicit;
7. protected durable effects require fresh commit-time authorization;
8. evaluator assets are isolated from candidate work;
9. every attempt references an immutable ContextPackage;
10. every loop has budget, no-progress and terminal conditions;
11. views/indexes/summaries are rebuildable;
12. autonomous policy cannot weaken safety or correctness.

## Reuse boundary

PAF reuses:

- Cline/OpenHands/other coding agents;
- LangGraph for adaptive graph execution;
- Temporal when durable distributed execution is actually required;
- MCP/native APIs for tools and A2A for remote opaque agents;
- OpenTelemetry, OPA and in-toto/SLSA where their capabilities are needed;
- native retrieval, Haystack/LlamaIndex, pgvector/Qdrant through context adapters;
- Optuna/Ray Tune/OpenEvolve-style systems through optional SearchPolicy adapters.

PAF retains semantic identity, authorization, evidence, recovery and assessment across all adapters.

## Context and RAG

RAG is not memory or truth. It constructs immutable ContextPackages from source snapshots.

```text
exact decision/object/path/symbol
→ structural relations
→ lexical/full-text retrieval
→ optional dense retrieval
→ fusion/reranking
→ policy and staleness filtering
→ ContextPackage
```

Initial implementation uses Git, ripgrep, project-native symbol indexes and SQLite FTS5. No vector service is required for the first campaign.

## Evaluation and completion

Routine coding uses a validation-profile `AssessmentProtocol`; research/optimization uses a fuller experiment profile. Protocol revisions are immutable.

One `PackageManifest` supports four profiles:

- Audit;
- Evidence;
- Reproduction;
- Completion.

## Correct bootstrap sequence

```text
BS-010  wire identity and canonical form
BS-012  native phase/run identity and monitoring
BS-014  typed ValidationActivity and receipts
BS-016  prerequisite preflight and explicit block/recovery operations
BS-018  partial-work manifests and compatibility recovery
BS-020  minimal reusable kernel contracts
```

The revision-9 additive installer repairs the current bootstrap enough to execute this backlog safely; it does not claim BS-012 through BS-018 are already product-complete.

## Novelty boundary

PAF's contribution is not autonomous coding itself. It is the portable, assurance-grade linkage of:

```text
engineering intent
→ dynamic work revisions
→ heterogeneous execution
→ exact context and evaluator identity
→ evidence and independent assessment
→ recovery and promotion scope
```

The core research test is whether the same engineering campaign remains credible, reproducible and comparable across different agents, backends and search strategies.
