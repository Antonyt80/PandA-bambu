import unittest
from paf.refinement import *
class Protocol(unittest.TestCase):
 def test_strict_and_lifecycle(self):
  r=RefinementRequest(('r',('s',),'system','id',None,True,'p',(),(),None)); p=RefinementProposal(('p',r.revision,('s',),'c',(),(),(),None)); v=RefinementReview(('v',p.revision,'c',True,(),(),'policy')); d=RefinementDecision(('d',p.revision,'c',v.revision,'accept','a',(),(),'policy'))
  self.assertTrue(validate_refinement(r,p,v,d).passed)
  with self.assertRaises(Exception): RefinementRequest.from_dict({'bad':1})
 def test_lifecycle_rejects_stale_subject_review_and_decision(self):
  r=RefinementRequest(('r',('s',),'system','id',None,True,'p',(),(),None)); p=RefinementProposal(('p',r.revision,('other',),'c',(),(),(),None))
  review=RefinementReview(('v','wrong','c',False,(),(),'policy')); decision=RefinementDecision(('d','wrong','c','wrong','reject','a',(),(),'policy'))
  codes=[x.code for x in validate_refinement(r,p,review,decision).issues]
  self.assertIn('stale-source',codes); self.assertIn('review-not-approved',codes); self.assertIn('subject-mismatch',codes)
 def test_unresolved_issue_requires_exact_admission(self):
  r=RefinementRequest(('r',('s',),'system','id',None,False,'p',(),(),None)); p=RefinementProposal(('p',r.revision,('s',),'c',(),({'issue_id':'open'},),(),None)); d=RefinementDecision(('d',p.revision,'c','none','accept','a',(),(),'policy'))
  self.assertIn('unresolved-issue-not-admitted',[x.code for x in validate_refinement(r,p,None,d).issues])
 def test_rejected_review_and_non_accepting_decision_fail(self):
  r=RefinementRequest(('r',('s',),'system','id',None,True,'p',(),(),None)); p=RefinementProposal(('p',r.revision,('s',),'c',(),(),(),None))
  review=RefinementReview(('v',p.revision,'c',False,(),(),'policy')); decision=RefinementDecision(('d',p.revision,'c',review.revision,'reject','a',(),(),'policy'))
  codes=[x.code for x in validate_refinement(r,p,review,decision).issues]
  self.assertIn('review-not-approved',codes); self.assertIn('decision-not-accepting',codes)
