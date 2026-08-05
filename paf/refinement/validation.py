"""Deterministic lifecycle and semantic-drift validation."""
from dataclasses import dataclass
from paf.kernel.errors import RefinementError
@dataclass(frozen=True,order=True)
class ValidationIssue: code:str; subject:str=""
@dataclass(frozen=True)
class ValidationReport:
    proposal_revision:str; candidate_revision:str; issues:tuple=()
    @property
    def passed(self): return not self.issues

def _changed_paths(before, after, path="$semantic-state"):
    """Return canonical structural changes; absence is intentionally observable."""
    if type(before) is dict and type(after) is dict:
        result=[]
        for key in sorted(set(before) | set(after)):
            if key not in before or key not in after:
                result.append((path + "." + key, before.get(key), after.get(key)))
            else:
                result.extend(_changed_paths(before[key], after[key], path + "." + key))
        return result
    if type(before) in (tuple,list) and type(after) in (tuple,list):
        # Lists are semantic collections in the common envelope.  Recording the
        # collection boundary avoids pretending positional changes are facts.
        return [] if tuple(before) == tuple(after) else [(path, before, after)]
    return [] if before == after else [(path, before, after)]

def _declares(change, path, before, after, baseline, candidate):
    if type(change) is not dict or not change.get("source_refs"):
        return False
    if change.get("semantic_key") == path and change.get("before") == before and change.get("after") == after:
        return True
    # Aggregate state records are auditable context, not a blanket admission for
    # individual differences.  Every changed semantic path needs its own exact,
    # source-linked declaration.
    return False

def validate_refinement(request,proposal,review,decision):
    issues=[]
    rd=request.to_dict(); pd=proposal.to_dict(); vd=review.to_dict() if review else None; dd=decision.to_dict() if decision else None
    if tuple(pd["source_revisions"]) != tuple(rd["source_revisions"]): issues.append(ValidationIssue("stale-source"))
    if pd["request_revision"] != request.revision: issues.append(ValidationIssue("subject-mismatch"))
    if rd["required_review"]:
        if not vd or vd["proposal_revision"] != proposal.revision or vd["candidate_revision"] != pd["candidate_revision"] or vd["approved"] is not True: issues.append(ValidationIssue("review-not-approved"))
    if not dd or dd["proposal_revision"] != proposal.revision or dd["candidate_revision"] != pd["candidate_revision"] or (vd and dd["review_revision"] != review.revision) or (not vd and dd["review_revision"] not in (None,"","none")): issues.append(ValidationIssue("subject-mismatch"))
    elif dd["outcome"] not in ("accept","accepted"): issues.append(ValidationIssue("decision-not-accepting"))
    admitted=() if not dd else tuple(dd["admitted_issue_ids"])
    for issue in pd["unresolved_issues"]:
        iid=issue.get("issue_id") if type(issue) is dict else issue
        if iid not in admitted: issues.append(ValidationIssue("unresolved-issue-not-admitted",str(iid)))
    changes=pd["semantic_changes"]
    for change in changes:
        if not isinstance(change,dict) or not change.get("source_refs") or (change.get("admission_required",True) and change.get("change_id") not in (() if not dd else tuple(dd["admitted_change_ids"]))): issues.append(ValidationIssue("semantic-change-unrecorded"))
    baseline=None; candidate=None
    for ref in pd["validation_refs"]:
        if type(ref) is dict and ref.get("kind")=="semantic-baseline": baseline=ref.get("value")
        if type(ref) is dict and ref.get("kind")=="semantic-candidate": candidate=ref.get("value")
    if baseline is not None or candidate is not None:
        if baseline is None or candidate is None: issues.append(ValidationIssue("semantic-change-unrecorded","missing-comparison"))
        elif baseline != candidate:
            for path, before, after in _changed_paths(baseline,candidate):
                if not any(_declares(change,path,before,after,baseline,candidate) for change in changes):
                    issues.append(ValidationIssue("semantic-change-unrecorded",path))
    return ValidationReport(proposal.revision,pd["candidate_revision"],tuple(sorted(issues)))
