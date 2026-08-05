"""Pure Work Graph proposal checks and all-or-nothing activation."""
from dataclasses import dataclass
from paf.kernel.errors import WorkGraphError, ActivationError
from paf.identity import TypedDigest
from paf.kernel.models import ModelEnvelope, ProposedWorkItem, ControllerIdAssignment, WorkGraphPayload
from paf.refinement.validation import ValidationReport
@dataclass(frozen=True)
class WorkGraphState:
    accepted_graph:ModelEnvelope; accepted_history:tuple=()
    def __post_init__(self): object.__setattr__(self,"accepted_history",tuple(self.accepted_history))
def _item_dict(item):
    return item.to_dict() if isinstance(item, ProposedWorkItem) else item

def _content(item):
    """Controller identity is assigned later and is not mutable item content."""
    material=_item_dict(item)
    if type(material) is not dict: return material
    return {key:value for key,value in material.items() if key != "controller_id"}

def _unsafe_bound(value):
    return type(value) is not str or not value or value == "/" or "*" in value or value.startswith("/")

def validate_work_items(items, assignments=(), completed_items=(), active_items=()):
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
        if any(_unsafe_bound(path) for path in item.allowed_paths): issues.append("overbroad-path")
        if any(_unsafe_bound(effect) for effect in item.allowed_effects): issues.append("overbroad-effect")
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
    proposed={item.logical_key:_content(item) for item in items}
    for prior in completed_items:
        prior=_item_dict(prior); key=prior.get("logical_key") if type(prior) is dict else None
        if key not in proposed: issues.append("completed-work-loss")
    for prior in active_items:
        prior=_item_dict(prior); key=prior.get("logical_key") if type(prior) is dict else None
        if key not in proposed or proposed[key] != _content(prior): issues.append("active-work-mutation")
    return tuple(sorted(set(issues)))

def _with_dependencies(items, dependencies):
    mapped={item.logical_key:tuple(item.dependencies) for item in items}
    for entry in dependencies:
        if type(entry) is dict:
            key=entry.get("logical_key"); deps=entry.get("dependencies")
        elif type(entry) in (tuple,list) and len(entry)==2:
            key,deps=entry
        else: raise WorkGraphError("malformed-dependency")
        if type(key) is not str or type(deps) not in (tuple,list): raise WorkGraphError("malformed-dependency")
        if key not in mapped: raise WorkGraphError("dangling-dependency")
        mapped[key]=tuple(deps)
    return tuple(ProposedWorkItem(item.logical_key,item.objective,item.inputs,item.outputs,mapped[item.logical_key],item.capabilities,item.allowed_paths,item.allowed_effects,item.trace_links,item.framework_reuse) for item in items)

def _proposal_content(items, refs, projection_revision):
    return {"items":[item.to_dict() for item in items],"source_revisions":list(refs),"projection_revision":projection_revision}

def build_work_graph_proposal(request,accepted_models,projection,proposed_items,proposed_dependencies=(),semantic_changes=()):
    if len(accepted_models)!=5 or {m.model_kind for m in accepted_models}!={"intent","problem","solution","system","activity"}: raise WorkGraphError("source-set-incomplete")
    if any(not isinstance(m,ModelEnvelope) or m.status!="accepted" for m in accepted_models): raise WorkGraphError("stale-source")
    refs=tuple(str(m.revision_id) for m in accepted_models)
    if len(refs) != len(set(refs)): raise WorkGraphError("source-set-incomplete")
    projection_refs=tuple(str(x.revision_id) if isinstance(x,ModelEnvelope) else str(x) for x in projection.accepted_models)
    if any(ref not in projection_refs for ref in refs): raise WorkGraphError("stale-source")
    if tuple(request.to_dict()["source_revisions"]) != refs: raise WorkGraphError("stale-source")
    if request.to_dict()["projection_revision"] != projection.revision: raise WorkGraphError("stale-source")
    items=_with_dependencies(tuple(proposed_items),proposed_dependencies)
    issues=validate_work_items(items,completed_items=projection.completed_work or (),active_items=projection.active_work or ())
    if issues: raise WorkGraphError(issues[0])
    content=_proposal_content(items,refs,projection.revision)
    candidate_revision=str(TypedDigest.for_value("paf:work-graph-proposal",content))
    validation_refs=({"kind":"work-graph-content","content":content},)
    from paf.refinement.protocol import RefinementProposal
    return RefinementProposal(("work-graph-proposal",request.revision,refs,candidate_revision,tuple(semantic_changes),(),validation_refs,None))

def _candidate_from_refs(proposal):
    for ref in proposal.to_dict()["validation_refs"]:
        if type(ref) is dict and ref.get("kind") == "accepted-work-graph" and type(ref.get("envelope")) is dict:
            try: return ModelEnvelope.from_dict(ref["envelope"])
            except Exception: raise ActivationError("malformed-candidate") from None
    return None

def _candidate_items(candidate):
    fields=candidate.payload.fields
    if len(fields) != 1 or type(fields[0]) is not dict or type(fields[0].get("items")) is not list: raise ActivationError("malformed-candidate")
    return fields[0]["items"]

def _proposed_items(items):
    names=("logical_key","objective","inputs","outputs","dependencies","capabilities","allowed_paths","allowed_effects","trace_links","framework_reuse")
    try:
        return tuple(ProposedWorkItem(**{name:item[name] for name in names}) for item in items)
    except Exception: raise ActivationError("malformed-candidate") from None

def _assigned_candidate(candidate, items, assignments):
    mapped={assignment.logical_key:str(assignment.controller_id) for assignment in assignments}
    assigned=[]
    for item in items:
        material=dict(item)
        material["controller_id"]=mapped[material["logical_key"]]
        assigned.append(material)
    return ModelEnvelope.create(
        model_id=candidate.model_id,
        status="accepted",
        payload=WorkGraphPayload(({"items":assigned},)),
        creation_metadata=candidate.creation_metadata,
        base_metadata=candidate.base_metadata,
        parents=(str(candidate.revision_id),),
        intent_ref=candidate.intent_ref,
        source_refs=candidate.source_refs,
        decision_refs=candidate.decision_refs,
        policy_refs=candidate.policy_refs,
        capability_refs=candidate.capability_refs,
        assumptions=candidate.assumptions,
        unknowns=candidate.unknowns,
        constraints=candidate.constraints,
        non_goals=candidate.non_goals,
        risks=candidate.risks,
        evidence_requirements=candidate.evidence_requirements,
    )

def activate_work_graph(current_state,expected_graph_revision,proposal,validation_report,review,decision,controller_assignments):
    if expected_graph_revision != str(current_state.accepted_graph.revision_id): raise ActivationError("stale-graph-revision")
    if not isinstance(validation_report,ValidationReport) or validation_report.proposal_revision != proposal.revision or validation_report.candidate_revision != proposal.to_dict()["candidate_revision"] or not validation_report.passed: raise ActivationError("subject-mismatch")
    lifecycle=validate_refinement_placeholder(proposal,review,decision)
    if lifecycle: raise ActivationError(lifecycle)
    candidate=_candidate_from_refs(proposal)
    if candidate is None or candidate.status not in ("proposed","accepted") or candidate.model_kind != "work-graph": raise ActivationError("missing-controller-id")
    if str(candidate.revision_id) != proposal.to_dict()["candidate_revision"]: raise ActivationError("subject-mismatch")
    items=_candidate_items(candidate)
    candidate_issues=validate_work_items(_proposed_items(items))
    if candidate_issues: raise ActivationError(candidate_issues[0])
    keys=[item.get("logical_key") for item in items if type(item) is dict]
    if len(keys) != len(items) or len(keys) != len(set(keys)): raise ActivationError("missing-controller-id")
    if len(controller_assignments) != len(items): raise ActivationError("missing-controller-id")
    try:
        mapped={assignment.logical_key:str(assignment.controller_id) for assignment in controller_assignments}
    except Exception: raise ActivationError("missing-controller-id") from None
    if set(mapped) != set(keys) or len(set(mapped.values())) != len(mapped): raise ActivationError("missing-controller-id")
    accepted=_assigned_candidate(candidate,items,controller_assignments)
    return WorkGraphState(accepted,current_state.accepted_history+(accepted.revision_id,))
def validate_refinement_placeholder(proposal,review,decision):
    if review is None or review.to_dict()["proposal_revision"] != proposal.revision or review.to_dict()["candidate_revision"] != proposal.to_dict()["candidate_revision"] or review.to_dict()["approved"] is not True:return "review-not-approved"
    d=decision.to_dict()
    if d["proposal_revision"] != proposal.revision or d["candidate_revision"] != proposal.to_dict()["candidate_revision"] or d["review_revision"] != review.revision:return "subject-mismatch"
    if d["outcome"] not in ("accept","accepted"):return "decision-not-accepting"
    return None
