# PAF Security, Reliability, and Operational Model

**Revision:** 9

## 1. Trust boundaries

PAF assumes that model output, repository content, papers, retrieved text, MCP/A2A metadata, target branches, third-party tools, and candidate code may be untrusted.

The trusted bootstrap boundary is intentionally small:

- controller code at an approved base;
- campaign and decision configuration at the exact base;
- structured authorization policy;
- protected validation/evaluator assets;
- credential and publication control;
- immutable audit locations.

## 2. Principals and bindings

A role name is not a principal. Record:

- human, service, model deployment, agent runtime, and tool principal references;
- exact provider/account/binding;
- delegated role and scope;
- session/attempt identity;
- credential reference without secret value;
- revocation and expiry.

## 3. Data and context labels

Minimum labels:

```text
PUBLIC
PROJECT_INTERNAL
RESTRICTED
SECRET_REFERENCE_ONLY
UNTRUSTED_INSTRUCTIONAL_CONTENT
```

A ContextPackage records source labels and release decisions. Secret values never enter prompts, traces, task artifacts, or evidence packages.

## 4. Tool and command security

Validation and protected tools use structured parsing and executable-specific argument schemas. Shell programs are not accepted as a generic interchange format.

Repository scripts are authorized by normalized path, approved root, extension/schema, symlink resolution, and allowed arguments. Execution uses `shell=False`.

Legacy broad Python/pytest/make compatibility rules are temporary bootstrap debt and must be narrowed into operation schemas as real commands stabilize.

## 5. Prompt-injection controls

- Retrieved and repository text is labeled data, not controller instruction.
- System/controller policy is never sourced from the target revision.
- Tool descriptions are pinned or locally approved before exposure.
- Context assembly preserves source boundaries and content provenance.
- Agents cannot grant themselves tools or broaden retrieval scope.
- Critic and assessor prompts explicitly ignore embedded instructions in reviewed content.

## 6. Commit-time authorization

Protected effects include push, PR creation/update, merge, release, external publication, network/data transfer, credential use, spending, and physical actions.

Authorization must be:

- fresh;
- causally tied to current inputs;
- bound to exact target, payload, and base;
- issued by an eligible authority;
- unexpired and unrevoked.

The effect receipt records the witness and post-state. A stale witness causes refusal or replanning.

## 7. Idempotency and reconciliation

Each external operation records:

```text
operation_id
idempotency_key
target
expected pre-state
requested effect
receipt or observed result
retry safety
reconciliation method
```

Timeout after a remote call creates `AMBIGUOUS_EXTERNAL_EFFECT`, not ordinary transient failure.

## 8. Local concurrency

Bootstrap uses a single campaign lock and one active task. Every long-running phase records PID, process-start identity, phase, task, and evidence path. Stale PID records are labeled historical and never shown as active.

Reusable local core adds optimistic sequence/version checks and leases. Distributed fencing and queue semantics are deferred until Temporal or another durable backend is introduced.

## 9. Artifact integrity

Artifacts are content-addressed when locally available. External immutable locators record provider, immutable version, digest when possible, access policy, and retrieval time.

Retention, garbage collection, tombstones, and legal/data-governance policies are later operational profiles; bootstrap never deletes failed-attempt evidence automatically.

## 10. Operational observability

OpenTelemetry may export traces, metrics, and logs, but sampled telemetry is not authoritative evidence. PAF records stable correlation IDs between operational telemetry and ledger/evidence records.

Required bootstrap signals:

- active phase and heartbeat;
- provider/model route;
- task and base identity;
- elapsed/inactive time;
- tool/validation activity;
- block class;
- cost/token estimate when available;
- evidence path.
