import unittest
from paf.identity import LogicalId, Namespace
from paf.kernel import *
from paf.control.work_graph import validate_work_items
class Graph(unittest.TestCase):
 def test_graph_rejections(self):
  a=ProposedWorkItem('a','a',dependencies=('b',),trace_links=('s',)); b=ProposedWorkItem('b','b',dependencies=('a',),trace_links=('s',))
  self.assertIn('dependency-cycle',validate_work_items((a,b)))
  self.assertIn('traceability-gap',validate_work_items((ProposedWorkItem('x','x'),)))
 def test_assignments(self):
  i=ProposedWorkItem('x','x',trace_links=('s',)); lid=LogicalId(Namespace('paf.test'),'work','x')
  self.assertEqual((),validate_work_items((i,),(ControllerIdAssignment('x',lid),)))
