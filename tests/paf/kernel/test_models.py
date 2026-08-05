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
 def test_semantic_categories_are_distinguishable_on_wire(self):
  claim=SourceClaim('x','v',('source',)); fact=Fact('x','v',('source',))
  self.assertNotEqual(claim.to_dict(),fact.to_dict())
  self.assertEqual(claim,SemanticRecord.from_dict(claim.to_dict()))
  with self.assertRaises(RecordError): Fact.from_dict(claim.to_dict())
 def test_extra_and_digest_tampering_fail(self):
  d=self.make(SystemPayload(())).to_dict(); d['extra']=True
  with self.assertRaises(ModelError): ModelEnvelope.from_dict(d)
  d=self.make(SystemPayload(())).to_dict(); d['content_digest']='td1:paf-json-v1:paf:model-content:sha256:'+'0'*64
  with self.assertRaises(ModelError): ModelEnvelope.from_dict(d)
 def test_malformed_payload_identity_and_revision_fail(self):
  d=self.make(ActivityPayload(())).to_dict(); d['payload']['kind']='intent'
  with self.assertRaises(ModelError): ModelEnvelope.from_dict(d)
  d=self.make(ActivityPayload(())).to_dict(); d['model_id']='lid1:paf.test:activity:other'
  with self.assertRaises(ModelError): ModelEnvelope.from_dict(d)
  d=self.make(ActivityPayload(())).to_dict(); d['revision_id']='rid1:paf.test:activity:paf-json-v1:sha256:'+'0'*64
  with self.assertRaises(ModelError): ModelEnvelope.from_dict(d)
 def test_all_semantic_categories_round_trip(self):
  categories=(SourceClaim,Fact,Interpretation,Assumption,Unknown,Conflict,Decision,Requirement,Constraint,Risk,NonGoal,EvidenceRequirement,AuthorityBoundary,TraceLink)
  for category in categories:
   record=category('key',{'value':'fixed'},('source',))
   self.assertEqual(record,SemanticRecord.from_dict(record.to_dict()))
 def test_uncanonicalizable_payload_fails(self):
  with self.assertRaises(ModelError): IntentPayload((float('nan'),))
 def test_semantic_change_normalizes_uncanonicalizable_values(self):
  with self.assertRaises(RecordError) as error: SemanticChange('c','scope-changed','x',float('nan'),None,('s',),'why')
  self.assertEqual('malformed-record',error.exception.code)