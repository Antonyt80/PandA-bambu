import unittest
from paf.refinement import *

class Validation(unittest.TestCase):
 def test_unadmitted_change_deterministic(self):
  r=RefinementRequest(('r',('s',),'system','id',None,False,'p',(),(),None)); p=RefinementProposal(('p',r.revision,('s',),'c',({'change_id':'x','source_refs':(), 'admission_required':True},),(),(),None)); d=RefinementDecision(('d',p.revision,'c','none','accept','a',(),(),'p')); a=validate_refinement(r,p,None,d); self.assertEqual(a,validate_refinement(r,p,None,d)); self.assertFalse(a.passed)
 def test_undeclared_semantic_drift_fails_closed(self):
  r=RefinementRequest(('r',('s',),'system','id',None,False,'p',(),(),None))
  refs=({'kind':'semantic-baseline','value':{'assumptions':['a']}},{'kind':'semantic-candidate','value':{'assumptions':[]}})
  p=RefinementProposal(('p',r.revision,('s',),'c',(),(),refs,None)); d=RefinementDecision(('d',p.revision,'c','none','accept','a',(),(),'p'))
  self.assertIn('semantic-change-unrecorded',[i.code for i in validate_refinement(r,p,None,d).issues])
 def test_exact_declared_source_linked_semantic_drift_can_pass(self):
  r=RefinementRequest(('r',('s',),'system','id',None,False,'p',(),(),None)); before={'unknowns':['u']}; after={'unknowns':[]}
  refs=({'kind':'semantic-baseline','value':before},{'kind':'semantic-candidate','value':after})
  change={'change_id':'resolved-u','classification':'unknown-removed','semantic_key':'$semantic-state.unknowns','before':['u'],'after':[],'source_refs':['s'],'rationale':'evidence','admission_required':True}
  p=RefinementProposal(('p',r.revision,('s',),'c',(change,),(),refs,None)); d=RefinementDecision(('d',p.revision,'c','none','accept','a',(),('resolved-u',),'p'))
  self.assertTrue(validate_refinement(r,p,None,d).passed)
 def test_aggregate_semantic_change_cannot_admit_multiple_differences(self):
  r=RefinementRequest(('r',('s',),'system','id',None,False,'p',(),(),None)); before={'requirements':['a','b'],'assumptions':[],'conflicts':['c']}; after={'requirements':['a'],'assumptions':['new'],'conflicts':[]}
  refs=({'kind':'semantic-baseline','value':before},{'kind':'semantic-candidate','value':after})
  aggregate={'change_id':'all','classification':'scope-changed','semantic_key':'$semantic-state','before':before,'after':after,'source_refs':['s'],'rationale':'coarse','admission_required':True}
  p=RefinementProposal(('p',r.revision,('s',),'c',(aggregate,),(),refs,None)); d=RefinementDecision(('d',p.revision,'c','none','accept','a',(),('all',),'p'))
  subjects={x.subject for x in validate_refinement(r,p,None,d).issues}
  self.assertEqual({'$semantic-state.assumptions','$semantic-state.conflicts','$semantic-state.requirements'},subjects)
 def test_unrequested_review_reference_is_subject_mismatch(self):
  r=RefinementRequest(('r',('s',),'system','id',None,False,'p',(),(),None)); p=RefinementProposal(('p',r.revision,('s',),'c',(),(),(),None)); d=RefinementDecision(('d',p.revision,'c','invented-review','accept','a',(),(),'p'))
  self.assertIn('subject-mismatch',[x.code for x in validate_refinement(r,p,None,d).issues])
 def test_missing_baseline_or_candidate_fails_closed(self):
  r=RefinementRequest(('r',('s',),'system','id',None,False,'p',(),(),None)); refs=({'kind':'semantic-baseline','value':{'conflicts':['c']}},)
  p=RefinementProposal(('p',r.revision,('s',),'c',(),(),refs,None)); d=RefinementDecision(('d',p.revision,'c','none','accept','a',(),(),'p'))
  self.assertIn('semantic-change-unrecorded',[x.code for x in validate_refinement(r,p,None,d).issues])
 def test_silent_narrowing_expansion_and_conflict_erasure_fail(self):
  r=RefinementRequest(('r',('s',),'system','id',None,False,'p',(),(),None)); before={'requirements':['a','b'],'conflicts':['c']}; after={'requirements':['a'],'conflicts':[]}
  p=RefinementProposal(('p',r.revision,('s',),'c',(),(),({'kind':'semantic-baseline','value':before},{'kind':'semantic-candidate','value':after}),None)); d=RefinementDecision(('d',p.revision,'c','none','accept','a',(),(),'p'))
  self.assertIn('semantic-change-unrecorded',[x.code for x in validate_refinement(r,p,None,d).issues])
 def test_unrecorded_assumption_and_decision_changes_fail(self):
  r=RefinementRequest(('r',('s',),'system','id',None,False,'p',(),(),None)); before={'assumptions':['a'],'decisions':[]}; after={'assumptions':[],'decisions':['d']}
  p=RefinementProposal(('p',r.revision,('s',),'c',(),(),({'kind':'semantic-baseline','value':before},{'kind':'semantic-candidate','value':after}),None)); d=RefinementDecision(('d',p.revision,'c','none','accept','a',(),(),'p'))
  subjects=[x.subject for x in validate_refinement(r,p,None,d).issues]
  self.assertIn('$semantic-state.assumptions',subjects); self.assertIn('$semantic-state.decisions',subjects)