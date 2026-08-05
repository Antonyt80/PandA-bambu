import unittest
from paf.refinement import *
class Protocol(unittest.TestCase):
 def test_strict_and_lifecycle(self):
  r=RefinementRequest(('r',('s',),'system','id',None,True,'p',(),(),None)); p=RefinementProposal(('p',r.revision,('s',),'c',(),(),(),None)); v=RefinementReview(('v',p.revision,'c',True,(),(),'policy')); d=RefinementDecision(('d',p.revision,'c',v.revision,'accept','a',(),(),'policy'))
  self.assertTrue(validate_refinement(r,p,v,d).passed)
  with self.assertRaises(Exception): RefinementRequest.from_dict({'bad':1})
