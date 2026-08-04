# PAF R1 wire identity and canonical form

This normative R1 profile defines portable identity only. It excludes EDA/HLS behavior, authority, signing, trust and attestation; a hash supports comparison, not authenticity.

## Decisions

**PAF-DEC-001 (resolved).** Namespaces are registered strict lowercase ASCII dot labels (`[a-z][a-z0-9-]*` per label): `paf` and `soda-evolve` are separate ordinary registrations. No case folding or display-name semantics exist. A legacy `evolvehls.agentic.foo` may be retained as migration source data and mapped to a `soda-evolve` logical ID.

**PAF-DEC-002 (resolved).** `paf-json-v1` is a PAF-owned restricted JSON-compatible profile, not RFC 8785. Values are null, booleans, safe signed integers `[-9007199254740991,9007199254740991]`, NFC Unicode scalar strings, binary, lists and string-keyed objects. Floats/decimals/non-finite values fail. Strings and keys NFC-normalize; post-normalization key collisions fail. Keys sort by scalar sequence, lists retain order; compact UTF-8 JSON has no BOM or whitespace. Binary is the reserved exact semantic tag `{"$paf-binary":"<unpadded-base64url>"}` and colliding ordinary objects fail. Duplicate JSON-text keys fail.

**PAF-DEC-003 (resolved).** Forms are `lid1:<namespace>:<kind>:<name>`, `rid1:<namespace>:<kind>:paf-json-v1:sha256:<64-lowercase-hex>`, and `td1:paf-json-v1:<domain>:sha256:<64-lowercase-hex>`; schema versions are nonnegative `major.minor` without leading zeroes. Parsing is full-input and alias-free. Digest preimage is `PAF-DIGEST-1 || frame("sha256") || frame(domain) || frame(profile) || frame(canonical-bytes)`, where every frame is an unsigned 64-bit big-endian length followed by bytes. Revision domains are `revision:<namespace>:<kind>`.

**PAF-DEC-004 (resolved).** Immutable registries explicitly register namespaces, profiles, schema versions, extensions and migration edges. Negotiation validates all identifiers and extensions before payload interpretation. Exact support succeeds; only a unique declared lossless route returns `migration-required`; unknown profile/namespace/schema/version/extension and ambiguity fail. No downgrade, inferred compatibility, automatic migration or field discard occurs. Unknown optional extensions require both preservable wire marking and explicit preservation; required unknown extensions fail.

**PAF-DEC-005 (resolved).** Python standard library is the reference and an independent Node standard-library reader verifies checked-in JSON vectors. A migration envelope retains complete source and target semantic values, source typed digest, operation, `lossless=true`, and extensions; mismatches, unknown/lossy/ambiguous operations, missing or extra fields fail. Migration is never ordinary interpretation and source retention permits rollback.

## Rejection and conformance

Stable codes include `invalid-namespace`, `invalid-schema-version`, `invalid-logical-id`, `invalid-revision-id`, `invalid-typed-digest`, `unsupported-semantic-type`, `integer-out-of-range`, `non-nfc-collision`, `invalid-unicode-scalar`, `duplicate-object-key`, `reserved-binary-tag`, `digest-mismatch`, `unknown-profile`, `unknown-namespace`, `unknown-schema`, `unknown-version`, `unknown-extension`, `ambiguous-migration`, and `lossy-migration`. `tests/paf/identity/vectors/paf_identity_v1.json` supplies fixed hex/wire expectations; human-readable IDs and digests are never canonical semantic bytes.
