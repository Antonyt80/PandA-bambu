"""Pure Work Graph proposal checks and all-or-nothing activation."""
from dataclasses import dataclass
from paf.kernel.errors import WorkGraphError, ActivationError
from paf.kernel.models import ModelEnvelope, WorkGraphPayload, ProposedWorkItem, AcceptedWorkItem, ControllerIdAssignment
from paf.refinement.validation import ValidationReport, validate_refinement
@dataclass(frozen=True)
class WorkGraphState:
    accepted_graph:ModelEnvelope; accepted_history:tuple=()
    def __post_init__(self): object.__setattr__(self,"accepted_history",tuple(self.accepted_history))
def validate_work_items(items, assignments=()):
    issues=[]; keys=[x.logical_key for x in items]
    if len(keys)!=len(set(keys)): issues.append("duplicate-logical-key")
    if any(not x.logical_key for x in items): issues.append("missing-controller-id")
    known=set(keys)
    for item in items:
        if not item.trace_links: issues.append("traceability-gap")
        for dep in item.dependencies:
            if dep not in known: issues.append("dangling-dependency")
            if dep==item.logical_key: issues.append("dependency-cycle")
        if any(x in ("scheduler","agent-loop","durable-workflow","retrieval") for x in item.framework_reuse): issues.append("framework-reinvention")
    graph={x.logical_key:tuple(x.dependencies) for x in items}
    visiting=set(); done=set()
    def visit(k):
        if k in visiting: return True
        if k in done:return False
        visiting.add(k); found=any(visit(d) for d in sorted(graph[k]) if d in graph); visiting.remove(k); done.add(k); return found
    if any(visit(k) for k in sorted(graph)): issues.append("dependency-cycle")
    if assignments:
        mapped=[x.logical_key for x in assignments]; ids=[str(x.controller_id) for x in assignments]
        if set(mapped)!=known: issues.append("missing-controller-id")
        if len(ids)!=len(set(ids)): issues.append("duplicate-controller-id")
    return tuple(sorted(set(issues)))
def build_work_graph_proposal(request,accepted_models,projection,proposed_items,proposed_dependencies=(),semantic_changes=()):
    if len(accepted_models)!=5 or {m.model_kind for m in accepted_models}!={"intent","problem","solution","system","activity"}: raise WorkGraphError("source-set-incomplete")
    if any(m.status!="accepted" for m in accepted_models): raise WorkGraphError("stale-source")
    refs=tuple(str(m.revision_id) for m in accepted_models)
    if tuple(request.to_dict()["source_revisions"]) != refs: raise WorkGraphError("stale-source")
    if request.to_dict()["projection_revision"] != projection.revision: raise WorkGraphError("stale-source")
    issues=validate_work_items(tuple(proposed_items))
    if issues: raise WorkGraphError(issues[0])
    # Caller supplies candidate revision externally; payload construction is intentionally not authority.
    from paf.refinement.protocol import RefinementProposal
    return RefinementProposal(("work-graph-proposal",request.revision,refs,"candidate-pending",tuple(semantic_changes),(),(),None))
def activate_work_graph(current_state,expected_graph_revision,proposal,validation_report,review,decision,controller_assignments):
    if expected_graph_revision != str(current_state.accepted_graph.revision_id): raise ActivationError("stale-graph-revision")
    if not isinstance(validation_report,ValidationReport) or validation_report.proposal_revision != proposal.revision or not validation_report.passed: raise ActivationError("subject-mismatch")
    lifecycle=validate_refinement_placeholder(proposal,review,decision)
    if lifecycle: raise ActivationError(lifecycle)
    payload=current_state.accepted_graph.payload
    if not isinstance(payload,WorkGraphPayload): raise ActivationError("model-payload-kind-mismatch")
    # Accepted candidate is caller-provided only as a complete model envelope encoded in proposal validation refs.
    candidate=None
    for ref in proposal.to_dict()["validation_refs"]:
        if isinstance(ref,ModelEnvelope): candidate=ref
    if candidate is None or candidate.status != "accepted" or candidate.model_kind != "work-graph": raise ActivationError("missing-controller-id")
    return WorkGraphState(candidate,current_state.accepted_history+(candidate.revision_id,))
def validate_refinement_placeholder(proposal,review,decision):
    if review is None or review.to_dict()["proposal_revision"] != proposal.revision or review.to_dict()["approved"] is not True:return "review-not-approved"
    d=decision.to_dict()
    if d["proposal_revision"] != proposal.revision:return "subject-mismatch"
    if d["outcome"] not in ("accept","accepted"):return "decision-not-accepting"
    return None
