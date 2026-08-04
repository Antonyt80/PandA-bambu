# PAF Literature and Framework Boundary

**Revision:** 9

## Autonomous engineering and evolution

Recent systems already demonstrate repository-grounded autonomous EDA modification, hierarchical paper-to-code execution, generate-review-repair loops, candidate archives, shared memory, evaluator-driven evolution, and full-flow QoR feedback. Representative systems include AuDoPEDA, VPR-Evolve, GR-Evolve, Self-Evolved ABC, SATLUTION, AlphaEvolve, CodeEvolve, SWE-Review, and HiRAS.

PAF therefore does not claim novelty for these individual mechanisms.

## Framework capability map

| Need | Reuse | PAF retains |
|---|---|---|
| Coding-agent execution | Cline, OpenHands, Claude Code/Codex-class tools | task/context/effect identity and assessment |
| Lightweight agent loop | OpenAI Agents SDK, PydanticAI | role and attempt bindings |
| Multi-agent messaging/orchestration | AutoGen / Microsoft Agent Framework, Semantic Kernel | semantic WorkItem and completion contracts |
| Adaptive state graph | LangGraph | accepted graph revisions and evidence identity |
| Durable distributed execution | Temporal; other durable systems through adapters | campaign semantics, idempotency, receipts, assessment |
| Tool interoperability | MCP/native APIs | trusted descriptors, authorization, effect classification |
| Remote opaque agents | A2A | delegation policy, exact task/evidence correlation |
| Telemetry | OpenTelemetry | authoritative ledger/evidence |
| Policy | typed local policy, OPA when justified | policy inputs, decisions, obligations, witnesses |
| Attestation | in-toto/SLSA | PAF predicate contents and package mapping |
| Experiment UI/tracking | MLflow/DVC | protocol and criterion semantics |
| Search/optimization | Optuna, Ray Tune, OpenEvolve, CodeEvolve | evaluator firewall, lineage, promotion |
| RAG/indexing | native indexes, Haystack, LlamaIndex, pgvector, Qdrant | source/context identity and retrieval audit |

## Stop-building rule

PAF implements a capability internally only when:

1. an adapter to a maintained external system was evaluated;
2. the external capability cannot preserve a required PAF invariant;
3. the gap is demonstrated in a real campaign;
4. the internal implementation is smaller and more maintainable than the workaround.

## Research evaluation direction

A strong PAF evaluation compares multiple execution/search strategies under the same intent, work, context, evaluator, and promotion contracts. The question is not whether PAF's own agent wins, but whether PAF preserves credible and portable engineering conclusions across agents and backends.
