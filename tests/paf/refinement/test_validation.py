import unittest
from paf.refinement import *
class Validation(unittest.TestCase):
 def test_unadmitted_change_deterministic(self):
  r=RefinementRequest(('r',('s',),'system','id',None,False,'p',(),(),None)); p=RefinementProposal(('p',r.revision,('s',),'c',({'change_id':'x','source_refs':(), 'admission_required':True},),(),(),None)); d=RefinementDecision(('d',p.revision,'c','none','accept','a',(),(),'p')); a=validate_refinement(r,p,None,d); self.assertEqual(a,validate_refinement(r,p,None,d)); self.assertFalse(a.passed)
