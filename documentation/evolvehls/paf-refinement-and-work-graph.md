# PAF refinement and Work Graph slice

`paf.kernel` exports exactly six typed model kinds: intent, problem, solution,
system (the architecture alias), activity, and work-graph. `ModelEnvelope` is a
strict schema-version-1 common envelope. Its typed payload never becomes a
generic knowledge object. It derives a BS-010 `RevisionId` and a
`paf:model-content` `TypedDigest` from material excluding those derived fields;
parsers reject unknown fields, kind mismatches, and tampering with stable codes.

`paf.refinement` supplies immutable `RefinementRequest`, `RefinementProposal`,
`RefinementReview`, `RefinementDecision`, and `validate_refinement`. These bind
exact revisions, required critique and accepting decisions. Semantic changes are
source-linked classifications and unresolved issues need exact admission. Each
semantic record carries an explicit category on the wire, so source claims,
facts, assumptions, unknowns, conflicts, decisions, and requirements remain
distinguishable after a canonical round trip.

`RepositoryStateProjection` is a caller-supplied, non-authoritative immutable
projection. `None` means unknown; `()` means observed known-empty. It invokes no
Git or services. Work Graph planners use logical keys only; controller IDs are
represented by `ControllerIdAssignment`. Graph checks cover traces, complete
unique identities, dependencies, cycles, bounded paths/effects, completed-work
preservation, active-work immutability, and explicitly declared framework reuse.

`activate_work_graph` is an in-memory compare-and-replace interface. It accepts
only a complete caller-supplied reviewed Work Graph candidate envelope, exact
approved review/decision subjects, a passing validation report, and a complete
unique controller-ID assignment. It derives the accepted immutable graph
revision only after every precondition succeeds. Failures leave the caller's
immutable state unchanged; success returns exactly one new immutable state. This slice is compatible with
`paf-json-v1`/BS-010 but does **not** provide runtime, persistence, authority
evaluation, critique execution, completion assessment, effect reconciliation,
checkpointing, publication, PR, or merge capability. Durable events, authority
policy, independent critique, completion assessment, effect reconciliation, and
publication remain explicit prerequisites.

Focused supported discovery does not require `tests/paf/__init__.py`:
`python3 -m unittest discover -s tests/paf -p 'test_*.py'` discovers the
authorized nested `kernel`, `refinement`, and `control` test packages.