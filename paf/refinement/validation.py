"""Deterministic lifecycle and declared-semantic-change validation."""
from dataclasses import dataclass
from paf.kernel.errors import RefinementError
@dataclass(frozen=True,order=True)
class ValidationIssue: code:str; subject:str=""
@dataclass(frozen=True)
class ValidationReport:
    proposal_revision:str; candidate_revision:str; issues:tuple=()
    @property
    def passed(self): return not self.issues

def validate_refinement(request,proposal,review,decision):
    issues=[]
    rd=request.to_dict(); pd=proposal.to_dict(); vd=review.to_dict() if review else None; dd=decision.to_dict() if decision else None
    if tuple(pd["source_revisions"]) != tuple(rd["source_revisions"]): issues.append(ValidationIssue("stale-source"))
    if pd["request_revision"] != request.revision: issues.append(ValidationIssue("subject-mismatch"))
    if rd["required_review"]:
        if not vd or vd["proposal_revision"] != proposal.revision or vd["candidate_revision"] != pd["candidate_revision"] or vd["approved"] is not True: issues.append(ValidationIssue("review-not-approved"))
    if not dd or dd["proposal_revision"] != proposal.revision or dd["candidate_revision"] != pd["candidate_revision"] or (vd and dd["review_revision"] != review.revision): issues.append(ValidationIssue("subject-mismatch"))
    elif dd["outcome"] not in ("accept","accepted"): issues.append(ValidationIssue("decision-not-accepting"))
    admitted=() if not dd else tuple(dd["admitted_issue_ids"])
    for issue in pd["unresolved_issues"]:
        iid=issue.get("issue_id") if type(issue) is dict else issue
        if iid not in admitted: issues.append(ValidationIssue("unresolved-issue-not-admitted",str(iid)))
    changes=pd["semantic_changes"]
    for change in changes:
        if not isinstance(change,dict) or not change.get("source_refs") or (change.get("admission_required",True) and change.get("change_id") not in (() if not dd else tuple(dd["admitted_change_ids"]))): issues.append(ValidationIssue("semantic-change-unrecorded"))
    return ValidationReport(proposal.revision,pd["candidate_revision"],tuple(sorted(issues)))
