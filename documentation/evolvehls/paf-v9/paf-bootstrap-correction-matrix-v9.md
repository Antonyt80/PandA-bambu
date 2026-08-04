# PAF Bootstrap Correction Matrix

**Revision:** 9  
**Purpose:** distinguish the additive bootstrap repair supplied in this pack from PAF product capabilities that still require autonomous implementation.

## Corrections implemented by `apply-paf-bootstrap-v9.py`

| Problem observed | Additive correction | Evidence/check |
|---|---|---|
| Model-generated `task_id` repeatedly rejected | Controller binds campaign ID, backlog ID, task ID, milestone, base branch, and dependencies before task validation | `identity-binding.json`; doctor checks binding order |
| Node `.mjs` validation rejected by raw prefix | `shlex` parsing and executable-specific Node rule for one `.js`/`.mjs`/`.cjs` script under `tests/paf/` or `scripts/paf/` | positive and adversarial unit tests |
| Generated validation commands converted to Bash | Campaign emits a JSON validation manifest; cycle calls `paf-run-validations`; runner uses `subprocess.run(argv, shell=False)` | production-cycle integration test and controller validation audit |
| Authorization lacked parsed audit evidence | Generation records executable, argv, rule ID, and normalized paths; execution records logs, timing, and exit status | `validation-authorizations.json` and `cycle-*-controller-validation-audit.json` |
| Task contract could proceed without independent review support | Recognized clean revision-3 campaign is upgraded to task review/remediation v2; existing review-capable campaign is preserved and patched structurally | doctor checks `task-review` and `revise-task` commands |
| Installed scripts could differ from repository scripts | Installer refreshes `~/.local/bin`; doctor compares hashes | `installed-match:*` doctor checks |
| `watch` could present an old cycle as active | Additive `paf-bootstrap-loop-v9` records exact child PID and process-start identity and labels terminal output historical | wrapper `status`/`watch`; later internalized by BS-012 |
| Bootstrap integrity was hard to diagnose | `paf-bootstrap-doctor-v9` performs structural, syntax, installed-copy, Node, unit, and production-cycle checks | `--full` report |

## Deliberately not claimed as implemented

| Capability | Why it remains work | Backlog item |
|---|---|---|
| Native durable phase/run identity in campaign state | The wrapper is additive scaffolding, not the final internal state model | BS-012 |
| Stable `ValidationActivity` and receipt contracts in reusable PAF | Current implementation is a bootstrap overlay | BS-014 |
| Decision prerequisite preflight before Terra | Current decisions are documents/configuration but the campaign does not yet enforce task prerequisites | BS-016 |
| Normative block taxonomy and distinct recovery commands | Current `retry` remains broader than the final design | BS-016 |
| Automatic partial-work checkpoint and compatibility recovery | Current preservation is manual/branch based | BS-018 |
| Append-only kernel ledger and reusable storage | Bootstrap remains atomic JSON/JSONL/Git by design | BS-020 onward |
| RAG/indexing framework | Retrieval contracts are designed; implementation begins deterministic-first later | BS-080 |
| OpenHands, LangGraph, or Temporal backends | Framework order is intentional; local semantics must stabilize first | BS-100, BS-112, later durability task |

## Compatibility limits

The installer is tested against:

1. the clean revision-3 bootstrap bundle;
2. revision-3 plus the task-review/remediation v2 campaign;
3. revision-3 plus task-review/remediation v2 and the prior controller-owned identity patch;
4. repeated idempotent installation after committing the first repair.

It fails closed when task-review support is absent and the campaign file is not the recognized clean revision-3 version, or when required structural anchors have changed.

It has **not** been executed against the user's current live `/workspaces/PandA-bambu` checkout. Run the doctor first, preserve any partial BS-010 work, and review the repair diff before committing.
