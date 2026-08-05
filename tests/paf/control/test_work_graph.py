import unittest
from paf.identity import LogicalId, Namespace
from paf.kernel import *
from paf.control import RepositoryStateProjection
from paf.control.work_graph import validate_work_items, build_work_graph_proposal, activate_work_graph, WorkGraphState
from paf.refinement import RefinementRequest, RefinementProposal, RefinementReview, RefinementDecision
from paf.refinement.validation import ValidationReport

class Graph(unittest.TestCase):
 def test_graph_rejections(self):
  a=ProposedWorkItem('a','a',dependencies=('b',),trace_links=('s',)); b=ProposedWorkItem('b','b',dependencies=('a',),trace_links=('s',))
  self.assertIn('dependency-cycle',validate_work_items((a,b)))
  self.assertIn('traceability-gap',validate_work_items((ProposedWorkItem('x','x'),)))
 def test_graph_rejects_dangling_duplicate_and_framework_reinvention(self):
  dangling=ProposedWorkItem('a','a',dependencies=('gone',),trace_links=('s',)); duplicate=ProposedWorkItem('a','other',trace_links=('s',)); bad=ProposedWorkItem('b','b',trace_links=('s',),framework_reuse=('scheduler',))
  codes=validate_work_items((dangling,duplicate,bad))
  self.assertIn('dangling-dependency',codes); self.assertIn('duplicate-logical-key',codes); self.assertIn('framework-reinvention',codes)
 def test_assignments(self):
  i=ProposedWorkItem('x','x',trace_links=('s',)); lid=LogicalId(Namespace('paf.test'),'work','x')
  self.assertEqual((),validate_work_items((i,),(ControllerIdAssignment('x',lid),)))
  self.assertIn('missing-controller-id',validate_work_items((i,),(ControllerIdAssignment('other',lid),)))
  self.assertIn('duplicate-controller-id',validate_work_items((i,ProposedWorkItem('y','y',trace_links=('s',)),),(ControllerIdAssignment('x',lid),ControllerIdAssignment('y',lid))))
 def test_bounds_completed_and_active_work_protections(self):
  safe=ProposedWorkItem('a','a',trace_links=('s',),allowed_paths=('paf/kernel',),allowed_effects=('write:workspace',))
  self.assertIn('overbroad-path',validate_work_items((ProposedWorkItem('a','a',trace_links=('s',),allowed_paths=('**',)),)))
  self.assertIn('overbroad-effect',validate_work_items((ProposedWorkItem('a','a',trace_links=('s',),allowed_effects=('/',)),)))
  self.assertIn('completed-work-loss',validate_work_items((),completed_items=(safe,)))
  changed=ProposedWorkItem('a','changed',trace_links=('s',),allowed_paths=('paf/kernel',),allowed_effects=('write:workspace',))
  self.assertIn('active-work-mutation',validate_work_items((changed,),active_items=(safe,)))
 def test_path_and_effect_root_and_wildcard_bounds_fail(self):
  for path in ('/','paf/**','../../etc','paf/../..'):
   self.assertIn('overbroad-path',validate_work_items((ProposedWorkItem('a','a',trace_links=('s',),allowed_paths=(path,)),)))
  for effect in ('/','write:*','../../effect'):
   self.assertIn('overbroad-effect',validate_work_items((ProposedWorkItem('a','a',trace_links=('s',),allowed_effects=(effect,)),)))
 def test_accepted_work_item_projection_is_retained_without_false_mutation(self):
  lid=LogicalId(Namespace('paf.test'),'work','a'); revision=self._graph('item',()).revision_id
  accepted=AcceptedWorkItem('a',lid,revision,self._graph('item',()).content_digest)
  proposed=ProposedWorkItem('a','a',trace_links=('s',))
  self.assertEqual((),validate_work_items((proposed,),completed_items=(accepted,),active_items=(accepted,)))
 def _models(self):
  result=[]
  for kind,cls in (('intent',IntentPayload),('problem',ProblemPayload),('solution',SolutionPayload),('system',SystemPayload),('activity',ActivityPayload)):
   result.append(ModelEnvelope.create(model_id=LogicalId(Namespace('paf.test'),kind,'current'),status='accepted',payload=cls(()),creation_metadata={'created':'fixed'},base_metadata={'base':'x'}))
  return tuple(result)
 def test_proposal_digest_and_dependencies_are_content_derived(self):
  models=self._models(); projection=RepositoryStateProjection('p','base',tuple(str(x.revision_id) for x in models))
  refs=tuple(str(x.revision_id) for x in models); request=RefinementRequest(('r',refs,'work-graph','graph',None,False,'p',(),(),projection.revision))
  a=ProposedWorkItem('a','a',trace_links=('s',)); b=ProposedWorkItem('b','b',trace_links=('s',))
  first=build_work_graph_proposal(request,models,projection,(a,b),(('b',('a',)),))
  second=build_work_graph_proposal(request,models,projection,(a,b),())
  self.assertNotEqual(first.to_dict()['candidate_revision'],second.to_dict()['candidate_revision'])
  self.assertEqual(['a'],first.to_dict()['validation_refs'][0]['content']['items'][1]['dependencies'])
 def test_atomic_activation_success_and_failure_preservation(self):
  current=self._graph('old',()); state=WorkGraphState(current,(current.revision_id,))
  item={'logical_key':'new','objective':'new','inputs':[],'outputs':[],'dependencies':[],'capabilities':[],'allowed_paths':['paf/kernel'],'allowed_effects':['write:workspace'],'trace_links':['s'],'framework_reuse':[]}
  candidate=self._graph('new',({'items':[item]},)); proposal=self._activation_proposal(candidate)
  review=RefinementReview(('review',proposal.revision,proposal.to_dict()['candidate_revision'],True,(),(),'policy'))
  decision=RefinementDecision(('decision',proposal.revision,proposal.to_dict()['candidate_revision'],review.revision,'accept','assessment',(),(),'policy'))
  report=ValidationReport(proposal.revision,proposal.to_dict()['candidate_revision']); assignment=ControllerIdAssignment('new',LogicalId(Namespace('paf.test'),'work','new'))
  next_state=activate_work_graph(state,str(current.revision_id),proposal,report,review,decision,(assignment,))
  self.assertNotEqual(next_state.accepted_graph,candidate); self.assertNotEqual(next_state.accepted_graph.revision_id,state.accepted_graph.revision_id); self.assertEqual(len(next_state.accepted_history),2)
  self.assertEqual('lid1:paf.test:work:new',next_state.accepted_graph.payload.fields[0]['items'][0]['controller_id'])
  with self.assertRaises(ActivationError): activate_work_graph(state,'rid1:paf.test:work-graph:paf-json-v1:sha256:'+'0'*64,proposal,report,review,decision,(assignment,))
  self.assertEqual(state,WorkGraphState(current,(current.revision_id,)))
 def test_activation_rejects_every_precondition_without_mutating_state(self):
  current=self._graph('old',()); state=WorkGraphState(current,(current.revision_id,)); candidate=self._graph('new',({'items':[]},)); proposal=self._activation_proposal(candidate)
  review=RefinementReview(('review',proposal.revision,proposal.to_dict()['candidate_revision'],True,(),(),'policy')); decision=RefinementDecision(('decision',proposal.revision,proposal.to_dict()['candidate_revision'],review.revision,'accept','assessment',(),(),'policy')); report=ValidationReport(proposal.revision,proposal.to_dict()['candidate_revision'])
  cases=((str(current.revision_id),ValidationReport('wrong','wrong'),review,decision,()),(str(current.revision_id),report,RefinementReview(('bad','wrong','wrong',False,(),(),'policy')),decision,()),(str(current.revision_id),report,review,RefinementDecision(('bad',proposal.revision,proposal.to_dict()['candidate_revision'],review.revision,'reject','a',(),(),'policy')),()))
  for expected,invalid_report,invalid_review,invalid_decision,assignments in cases:
   with self.assertRaises(ActivationError): activate_work_graph(state,expected,proposal,invalid_report,invalid_review,invalid_decision,assignments)
   self.assertEqual(state,WorkGraphState(current,(current.revision_id,)))
 def test_activation_rejects_candidate_subject_and_controller_id_defects(self):
  current=self._graph('old',()); state=WorkGraphState(current,(current.revision_id,)); candidate=self._graph('new',({'items':[ProposedWorkItem('a','a',trace_links=('s',)).to_dict()]},)); proposal=self._activation_proposal(candidate)
  review=RefinementReview(('review',proposal.revision,proposal.to_dict()['candidate_revision'],True,(),(),'policy')); decision=RefinementDecision(('decision',proposal.revision,proposal.to_dict()['candidate_revision'],review.revision,'accept','assessment',(),(),'policy')); report=ValidationReport(proposal.revision,proposal.to_dict()['candidate_revision'])
  wrong=RefinementProposal(('proposal','request',(),str(current.revision_id),(),(),({'kind':'accepted-work-graph','envelope':candidate.to_dict()},),None))
  duplicate=(ControllerIdAssignment('a',LogicalId(Namespace('paf.test'),'work','one')),ControllerIdAssignment('a',LogicalId(Namespace('paf.test'),'work','two')))
  with self.assertRaises(ActivationError): activate_work_graph(state,str(current.revision_id),wrong,ValidationReport(wrong.revision,str(current.revision_id)),review,decision,())
  with self.assertRaises(ActivationError): activate_work_graph(state,str(current.revision_id),proposal,report,review,decision,duplicate)
  self.assertEqual(state,WorkGraphState(current,(current.revision_id,)))
 def test_activation_preserves_prior_items_and_builder_proposals_interoperate(self):
  prior=ProposedWorkItem('done','done',trace_links=('s',)).to_dict(); current=self._graph('old',({'items':[prior]},)); state=WorkGraphState(current,(current.revision_id,))
  dropped=self._graph('new',({'items':[]},)); dropped_proposal=self._activation_proposal(dropped)
  review=RefinementReview(('review',dropped_proposal.revision,dropped_proposal.to_dict()['candidate_revision'],True,(),(),'policy')); decision=RefinementDecision(('decision',dropped_proposal.revision,dropped_proposal.to_dict()['candidate_revision'],review.revision,'accept','assessment',(),(),'policy')); report=ValidationReport(dropped_proposal.revision,dropped_proposal.to_dict()['candidate_revision'])
  with self.assertRaises(ActivationError) as error: activate_work_graph(state,str(current.revision_id),dropped_proposal,report,review,decision,())
  self.assertIn(error.exception.code,('active-work-mutation','completed-work-loss')); self.assertIn('completed-work-loss',validate_work_items((),completed_items=(prior,))); self.assertEqual(state,WorkGraphState(current,(current.revision_id,)))
  active=dict(prior,controller_id='lid1:paf.test:work:stable'); active_current=self._graph('active',({'items':[active]},)); active_state=WorkGraphState(active_current,(active_current.revision_id,)); same_content=self._graph('same',({'items':[prior]},)); active_proposal=self._activation_proposal(same_content)
  active_review=RefinementReview(('active-review',active_proposal.revision,active_proposal.to_dict()['candidate_revision'],True,(),(),'policy')); active_decision=RefinementDecision(('active-decision',active_proposal.revision,active_proposal.to_dict()['candidate_revision'],active_review.revision,'accept','assessment',(),(),'policy')); active_report=ValidationReport(active_proposal.revision,active_proposal.to_dict()['candidate_revision'])
  with self.assertRaises(ActivationError) as error: activate_work_graph(active_state,str(active_current.revision_id),active_proposal,active_report,active_review,active_decision,(ControllerIdAssignment('done',LogicalId(Namespace('paf.test'),'work','changed')),))
  self.assertEqual('active-work-mutation',error.exception.code); self.assertEqual(active_state,WorkGraphState(active_current,(active_current.revision_id,)))
  models=self._models(); projection=RepositoryStateProjection('p','base',tuple(str(x.revision_id) for x in models)); refs=tuple(str(x.revision_id) for x in models); request=RefinementRequest(('r',refs,'work-graph','graph',None,False,'p',(),(),projection.revision))
  proposal=build_work_graph_proposal(request,models,projection,(ProposedWorkItem('done','done',trace_links=('s',)),))
  review=RefinementReview(('builder-review',proposal.revision,proposal.to_dict()['candidate_revision'],True,(),(),'policy')); decision=RefinementDecision(('builder-decision',proposal.revision,proposal.to_dict()['candidate_revision'],review.revision,'accept','assessment',(),(),'policy')); report=ValidationReport(proposal.revision,proposal.to_dict()['candidate_revision']); assignment=ControllerIdAssignment('done',LogicalId(Namespace('paf.test'),'work','done'))
  self.assertEqual('accepted',activate_work_graph(state,str(current.revision_id),proposal,report,review,decision,(assignment,)).accepted_graph.status)
 def test_proposal_rejects_incomplete_proposed_and_superseded_sources(self):
  models=self._models(); projection=RepositoryStateProjection('p','base',tuple(str(x.revision_id) for x in models)); refs=tuple(str(x.revision_id) for x in models); request=RefinementRequest(('r',refs,'work-graph','graph',None,False,'p',(),(),projection.revision)); item=ProposedWorkItem('a','a',trace_links=('s',))
  with self.assertRaises(WorkGraphError): build_work_graph_proposal(request,models[:4],projection,(item,))
  proposed=ModelEnvelope.create(model_id=LogicalId(Namespace('paf.test'),'intent','future'),status='proposed',payload=IntentPayload(()),creation_metadata={'created':'fixed'},base_metadata={'base':'x'})
  with self.assertRaises(WorkGraphError): build_work_graph_proposal(request,(proposed,)+models[1:],projection,(item,))
  stale_projection=RepositoryStateProjection('p','base',())
  with self.assertRaises(WorkGraphError): build_work_graph_proposal(request,models,stale_projection,(item,))
 def _graph(self,name,fields):
  return ModelEnvelope.create(model_id=LogicalId(Namespace('paf.test'),'work-graph',name),status='accepted',payload=WorkGraphPayload(fields),creation_metadata={'created':'fixed'},base_metadata={'base':'x'})
 def _activation_proposal(self,candidate):
  from paf.refinement import RefinementProposal
  return RefinementProposal(('proposal','request',(),str(candidate.revision_id),(),(),({'kind':'accepted-work-graph','envelope':candidate.to_dict()},),None))