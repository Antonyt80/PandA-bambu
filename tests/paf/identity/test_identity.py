import unittest
from paf.identity import *
class IdentityTests(unittest.TestCase):
 def test_values_and_separation(self):
  l=LogicalId.parse('lid1:paf:artifact:alpha'); self.assertEqual(str(l),'lid1:paf:artifact:alpha'); self.assertNotEqual(l,RevisionId(Namespace('paf'),'artifact','paf-json-v1','sha256',b'x'*32)); self.assertEqual(str(SchemaVersion.parse('1.0')),'1.0')
  for x in ('PAF','a..b','a-'): 
   with self.assertRaises(IdentityError): Namespace(x)
 def test_canonical(self):
  self.assertEqual(canonical_bytes({'b':1,'a':'é'}),b'{"a":"\xc3\xa9","b":1}')
  self.assertEqual(canonical_bytes(BinaryValue(b'\x01\x02')),b'{"$paf-binary":"AQI"}')
  with self.assertRaises(CanonicalizationError): canonical_bytes(1.2)
  with self.assertRaises(CanonicalizationError): canonicalize_json_text('{"a":1,"a":2}')
 def test_digest(self):
  d=TypedDigest.for_value('example',{'b':2,'a':1}); self.assertEqual(str(d),'td1:paf-json-v1:example:sha256:26cc1f90e974c151b8fa54d6265370bc388c64993679e40fe5b4da19eb776c5d'); self.assertTrue(d.verify({'a':1,'b':2}))
  with self.assertRaises(DigestError): d.verify({'a':2})
 def test_negotiation(self):
  r=IdentityRegistry().register_namespace('paf').register_schema('paf','thing','1.0').freeze()
  self.assertEqual(negotiate(r,NegotiationOffer('paf','thing','1.0')).status,'exact-compatible')
  with self.assertRaises(NegotiationError): negotiate(r,NegotiationOffer('paf','thing','1.1'))
