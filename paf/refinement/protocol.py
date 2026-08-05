"""Strict, caller-driven refinement lifecycle records."""
from dataclasses import dataclass
from paf.identity import TypedDigest
from paf.kernel.errors import RefinementError
from paf.kernel.records import exact, wire

def _record(cls, name, fields):
    @dataclass(frozen=True)
    class R:
        values: tuple
        def __post_init__(self):
            if len(self.values)!=len(fields): raise RefinementError("malformed-record")
        def to_dict(self): return dict(zip(fields,wire(self.values)))
        @classmethod
        def from_dict(c,d):
            exact(d,fields,RefinementError); return c(tuple(d[x] for x in fields))
        @property
        def revision(self): return str(TypedDigest.for_value("paf:"+name,self.to_dict()))
    R.__name__=cls; return R
RefinementRequest=_record("RefinementRequest","refinement-request",("request_id","source_revisions","target_kind","target_id","expected_revision","required_review","review_profile","constraints","policy_refs","projection_revision"))
RefinementProposal=_record("RefinementProposal","refinement-proposal",("proposal_id","request_revision","source_revisions","candidate_revision","semantic_changes","unresolved_issues","validation_refs","repair_of"))
RefinementReview=_record("RefinementReview","refinement-review",("review_id","proposal_revision","candidate_revision","approved","findings","unresolved_issues","policy_ref"))
RefinementDecision=_record("RefinementDecision","refinement-decision",("decision_id","proposal_revision","candidate_revision","review_revision","outcome","assessment_ref","admitted_issue_ids","admitted_change_ids","policy_ref"))
