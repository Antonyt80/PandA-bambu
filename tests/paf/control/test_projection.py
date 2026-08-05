import unittest
from paf.control import RepositoryStateProjection
from paf.kernel.errors import ProjectionError
class Projection(unittest.TestCase):
 def test_unknown_distinct_and_deterministic(self):
  source=['r']; p=RepositoryStateProjection('p','base',('a',),None,(),source_refs=source); source.append('x')
  self.assertIsNone(p.completed_work); self.assertEqual(p.active_work,()); self.assertEqual(p.source_refs,('r',)); self.assertEqual(p.revision,p.revision)
 def test_uncanonicalizable_value_has_stable_projection_failure(self):
  with self.assertRaises(ProjectionError) as error: RepositoryStateProjection('p','base',(),history=float('nan'))
  self.assertEqual('malformed-record',error.exception.code)
