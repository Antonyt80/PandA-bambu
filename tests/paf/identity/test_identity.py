import unittest

from paf.identity import (BinaryValue, CanonicalizationError, ExtensionEnvelope, IdentityRegistry,
    IdentitySyntaxError, LogicalId, MigrationEnvelope, Namespace, NegotiationError,
    NegotiationOffer, RegistryError, RevisionId, SchemaKey, SchemaVersion, TypedDigest,
    canonical_bytes, canonicalize_json_text, negotiate, parse_json_text, revision_for, verify_revision)


class IdentityTests(unittest.TestCase):
    def assertCode(self, code, function, *args):
        with self.assertRaises(Exception) as caught: function(*args)
        self.assertEqual(code, caught.exception.code)

    def registry(self, preserve=False):
        registry = IdentityRegistry().register_profile("paf-json-v1")
        registry.register_namespace("paf").register_namespace("soda-evolve")
        registry.register_schema("paf", "item", "2.0")
        registry.register_schema("soda-evolve", "item", "1.0")
        registry.set_unknown_optional_extension_preservation(preserve)
        return registry

    def test_value_types_are_distinct_ordered_and_alias_free(self):
        logical = LogicalId(Namespace("paf"), "item", "A-1")
        self.assertEqual(logical, LogicalId.parse("lid1:paf:item:A-1"))
        self.assertLess(LogicalId(Namespace("paf"), "item", "A"), logical)
        self.assertNotEqual(logical, revision_for("paf", "item", {"name": "A-1"}))
        self.assertCode("invalid-logical-id", LogicalId.parse, "lid1:PAF:item:A")
        self.assertCode("invalid-namespace", Namespace, "Paf")
        self.assertCode("invalid-schema-version", SchemaVersion.parse, "01.0")
        self.assertCode("invalid-revision-id", RevisionId.parse, "rid1:paf:item:paf-json-v1:sha256:" + "A" * 64)

    def test_digest_domain_framing_revision_and_tamper(self):
        digest = TypedDigest.for_value("revision:paf:item", {"a": 1})
        self.assertEqual(digest, TypedDigest.parse(str(digest)))
        self.assertCode("invalid-typed-digest", TypedDigest.parse, str(digest).replace("sha256", "SHA256"))
        revision = revision_for("paf", "item", {"a": 1})
        self.assertTrue(verify_revision(revision, {"a": 1}))
        self.assertCode("digest-mismatch", verify_revision, revision, {"a": 2})
        self.assertNotEqual(TypedDigest.for_value("one", {"a": 1}), TypedDigest.for_value("two", {"a": 1}))

    def test_canonical_domain_binary_and_json_text(self):
        self.assertEqual(canonical_bytes({"e\u0301": 1}), canonical_bytes({"é": 1}))
        self.assertEqual(b'{"$paf-binary":"AQI"}', canonical_bytes(BinaryValue(b"\x01\x02")))
        self.assertEqual(canonical_bytes(BinaryValue(b"\x01\x02")), canonicalize_json_text('{"$paf-binary":"AQI"}'))
        self.assertIsInstance(parse_json_text('{"$paf-binary":""}'), BinaryValue)
        self.assertCode("reserved-binary-tag", canonical_bytes, {"$paf-binary": "AQI"})
        self.assertCode("invalid-binary", canonicalize_json_text, '{"$paf-binary":"AQ="}')
        self.assertCode("invalid-binary", canonicalize_json_text, '{"$paf-binary":"AB"}')
        self.assertCode("duplicate-object-key", canonicalize_json_text, '{"a":1,"a":2}')
        self.assertCode("non-nfc-collision", canonicalize_json_text, '{"e\\u0301":1,"é":2}')
        self.assertCode("non-nfc-collision", canonical_bytes, {"e\u0301": 1, "é": 2})
        self.assertCode("unsupported-semantic-type", canonical_bytes, 1.5)
        self.assertCode("invalid-json-text", canonicalize_json_text, b"\xef\xbb\xbf{}")
        for value in (-9007199254740992, 9007199254740992):
            self.assertCode("integer-out-of-range", canonical_bytes, value)
        self.assertCode("invalid-unicode-scalar", canonicalize_json_text, '"\\ud800"')

    def test_registry_freezes_and_keeps_namespaces_independent(self):
        registry = self.registry().freeze()
        self.assertIn(Namespace("paf"), registry.namespaces)
        self.assertIn(Namespace("soda-evolve"), registry.namespaces)
        self.assertCode("registry-frozen", registry.register_namespace, "third")
        with self.assertRaises(AttributeError): registry.namespaces.add(Namespace("third"))

    def test_negotiation_exact_migration_and_extensions(self):
        registry = self.registry(True)
        source = SchemaKey(Namespace("paf"), "item", SchemaVersion(1, 0))
        target = SchemaKey(Namespace("paf"), "item", SchemaVersion(2, 0))
        registry.add_migration(source, target, "upgrade").freeze()
        self.assertEqual("exact-compatible", negotiate(registry, NegotiationOffer(Namespace("paf"), "item", SchemaVersion(2, 0))).status)
        self.assertEqual("migration-required", negotiate(registry, NegotiationOffer(Namespace("paf"), "item", SchemaVersion(1, 0))).status)
        optional = ExtensionEnvelope("unknown", False, True, {"x": 1})
        self.assertEqual("exact-compatible", negotiate(registry, NegotiationOffer(Namespace("paf"), "item", SchemaVersion(2, 0), extensions=(optional,))).status)
        self.assertCode("unknown-extension", negotiate, registry, NegotiationOffer(Namespace("paf"), "item", SchemaVersion(2, 0), extensions=(ExtensionEnvelope("unknown", True, True, {}),)))
        self.assertCode("unknown-profile", negotiate, registry, NegotiationOffer(Namespace("paf"), "item", SchemaVersion(2, 0), "other-profile"))
        self.assertCode("duplicate-extension", NegotiationOffer, Namespace("paf"), "item", SchemaVersion(2, 0), "paf-json-v1", (optional, optional))

    def test_negotiation_result_and_known_extension_contract_are_strict(self):
        registry = self.registry().register_extension("known", True).freeze()
        self.assertCode("malformed-extension", negotiate, registry,
                        NegotiationOffer(Namespace("paf"), "item", SchemaVersion(2, 0),
                                         extensions=(ExtensionEnvelope("known", False, False, {}),)))
        from paf.identity import NegotiationResult
        self.assertCode("malformed-negotiation-result", NegotiationResult, "exact-compatible", "ok", "unexpected")
        self.assertCode("malformed-negotiation-result", NegotiationResult, "migration-required")

    def test_migration_envelope_retains_and_verifies_source(self):
        source = {"version": 1, "data": [1]}; target = {"version": 2, "data": [1]}
        digest = TypedDigest.for_value("migration:paf:item", source)
        envelope = MigrationEnvelope(source, target, digest, "upgrade", True, (ExtensionEnvelope("note", False, True, {}),))
        self.assertIs(envelope.source, source)
        self.assertCode("digest-mismatch", MigrationEnvelope, source, target, TypedDigest.for_value("migration:paf:item", {"x": 1}), "upgrade", True)
        self.assertCode("lossy-migration", MigrationEnvelope, source, target, digest, "upgrade", False)
        self.assertCode("unexpected-envelope-field", MigrationEnvelope.from_dict, {"source": source})


if __name__ == "__main__": unittest.main()