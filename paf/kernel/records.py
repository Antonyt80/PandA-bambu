"""Immutable strict records shared by PAF models."""
from dataclasses import dataclass
from paf.identity import canonical_bytes
from .errors import RecordError

def exact(data, fields, error=RecordError):
    if type(data) is not dict: raise error("malformed-record")
    if set(data) != set(fields): raise error("unexpected-record-field")
def wire(value):
    if hasattr(value, "to_dict"): return value.to_dict()
    if isinstance(value, tuple): return [wire(x) for x in value]
    if isinstance(value, list): return [wire(x) for x in value]
    if isinstance(value, dict): return {key: wire(child) for key, child in value.items()}
    return value

def _tuple(value, name):
    if type(value) not in (tuple, list): raise RecordError("malformed-record")
    return tuple(value)
@dataclass(frozen=True)
class SemanticRecord:
    key: str; value: object; source_refs: tuple=()
    def __post_init__(self):
        if type(self.key) is not str or not self.key or type(self.source_refs) not in (tuple,list): raise RecordError("malformed-record")
        object.__setattr__(self,"source_refs",tuple(self.source_refs))
        try: canonical_bytes(self.to_dict())
        except Exception: raise RecordError("malformed-record") from None
    def to_dict(self): return {"category":self.__class__.__name__,"key":self.key,"value":wire(self.value),"source_refs":list(self.source_refs)}
    @classmethod
    def from_dict(cls,data):
        exact(data,("category","key","value","source_refs"))
        category=_SEMANTIC_CATEGORIES.get(data["category"])
        if category is None or (cls is not SemanticRecord and category is not cls): raise RecordError("semantic-category-mismatch")
        if type(data["source_refs"]) is not list: raise RecordError("malformed-record")
        return category(data["key"],data["value"],tuple(data["source_refs"]))
# Named types retain otherwise-identical semantic values without collapsing categories.
class SourceClaim(SemanticRecord): pass
class Fact(SemanticRecord): pass
class Interpretation(SemanticRecord): pass
class Assumption(SemanticRecord): pass
class Unknown(SemanticRecord): pass
class Conflict(SemanticRecord): pass
class Decision(SemanticRecord): pass
class Requirement(SemanticRecord): pass
class Constraint(SemanticRecord): pass
class Risk(SemanticRecord): pass
class NonGoal(SemanticRecord): pass
class EvidenceRequirement(SemanticRecord): pass
class AuthorityBoundary(SemanticRecord): pass
class TraceLink(SemanticRecord): pass
_SEMANTIC_CATEGORIES={c.__name__:c for c in (SourceClaim,Fact,Interpretation,Assumption,Unknown,Conflict,Decision,Requirement,Constraint,Risk,NonGoal,EvidenceRequirement,AuthorityBoundary,TraceLink)}
@dataclass(frozen=True)
class SemanticChange:
    change_id:str; classification:str; semantic_key:str; before:object; after:object; source_refs:tuple; rationale:str; admission_required:bool=True
    def __post_init__(self):
        allowed=("narrowing","expansion","assumption-added","assumption-removed","decision-added","decision-removed","conflict-added","conflict-removed","unknown-added","unknown-removed","requirement-changed","scope-changed","path-changed","effect-changed")
        if type(self.change_id) is not str or not self.change_id or self.classification not in allowed or type(self.semantic_key) is not str or type(self.source_refs) not in (tuple,list) or type(self.rationale) is not str or type(self.admission_required) is not bool: raise RecordError("malformed-record")
        object.__setattr__(self,"source_refs",tuple(self.source_refs)); canonical_bytes(self.to_dict())
    def to_dict(self): return {"change_id":self.change_id,"classification":self.classification,"semantic_key":self.semantic_key,"before":wire(self.before),"after":wire(self.after),"source_refs":list(self.source_refs),"rationale":self.rationale,"admission_required":self.admission_required}
    @classmethod
    def from_dict(cls,d):
        exact(d,("change_id","classification","semantic_key","before","after","source_refs","rationale","admission_required")); return cls(d["change_id"],d["classification"],d["semantic_key"],d["before"],d["after"],tuple(d["source_refs"]),d["rationale"],d["admission_required"])
@dataclass(frozen=True)
class UnresolvedIssue:
    issue_id:str; description:str; admissible:bool=False
    def __post_init__(self):
        if type(self.issue_id) is not str or type(self.description) is not str or type(self.admissible) is not bool: raise RecordError("malformed-record")
    def to_dict(self): return {"issue_id":self.issue_id,"description":self.description,"admissible":self.admissible}
    @classmethod
    def from_dict(cls,d): exact(d,("issue_id","description","admissible")); return cls(**d)
