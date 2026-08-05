import unittest
from paf.identity import LogicalId, Namespace, canonical_bytes
from paf.kernel import *
class Models(unittest.TestCase):
 def make(self,p): return ModelEnvelope.create(model_id=LogicalId(Namespace('paf.test'),p.KIND,'one'),status='proposed',payload=p,creation_metadata={'created':'fixed'},base_metadata={'base':'x'})
 def test_six_round_trip(self):
  for c in (IntentPayload,ProblemPayload,SolutionPayload,SystemPayload,ActivityPayload,WorkGraphPayload):
   e=self.make(c(({'semantic':'value'},))); self.assertEqual(e,ModelEnvelope.from_dict(e.to_dict())); self.assertEqual(canonical_bytes(e.to_dict()),canonical_bytes(ModelEnvelope.from_dict(e.to_dict()).to_dict()))
 def test_tamper_and_cross_kind_fail(self):
  e=self.make(IntentPayload(())); d=e.to_dict(); d['status']='accepted'
  with self.assertRaises(ModelError): ModelEnvelope.from_dict(d)
  with self.assertRaises(ModelError): ModelEnvelope.create(model_id=e.model_id,status='proposed',payload=ProblemPayload(()),creation_metadata={},base_metadata={})
