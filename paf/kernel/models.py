"""The six typed PAF v11 model payloads and signed common envelope."""
from dataclasses import dataclass
from paf.identity import LogicalId, RevisionId, TypedDigest, revision_for, canonical_bytes
from .errors import ModelError
from .records import exact, wire
MODEL_KINDS=("intent","problem","solution","system","activity","work-graph")

def _list(v):
    if type(v) not in (tuple,list): raise ModelError("malformed-record")
    return tuple(v)
@dataclass(frozen=True)
class Payload:
    fields: tuple=()
    KIND=""
    def __post_init__(self):
        object.__setattr__(self,"fields",_list(self.fields))
        try: canonical_bytes(self.to_dict())
        except Exception: raise ModelError("malformed-record") from None
    def to_dict(self): return {"kind":self.KIND,"fields":wire(self.fields)}
    @classmethod
    def from_dict(cls,d):
        exact(d,("kind","fields"),ModelError)
        if d["kind"] != cls.KIND or type(d["fields"]) is not list: raise ModelError("model-payload-kind-mismatch")
        return cls(tuple(d["fields"]))
class IntentPayload(Payload): KIND="intent"
class ProblemPayload(Payload): KIND="problem"
class SolutionPayload(Payload): KIND="solution"
class SystemPayload(Payload): KIND="system"
class ActivityPayload(Payload): KIND="activity"
class WorkGraphPayload(Payload): KIND="work-graph"
_PAYLOADS={x.KIND:x for x in (IntentPayload,ProblemPayload,SolutionPayload,SystemPayload,ActivityPayload,WorkGraphPayload)}
@dataclass(frozen=True)
class ProposedWorkItem:
    logical_key:str; objective:str; inputs:tuple=(); outputs:tuple=(); dependencies:tuple=(); capabilities:tuple=(); allowed_paths:tuple=(); allowed_effects:tuple=(); trace_links:tuple=(); framework_reuse:tuple=()
    def __post_init__(self):
        if type(self.logical_key) is not str or not self.logical_key or type(self.objective) is not str: raise ModelError("malformed-record")
        for n in ("inputs","outputs","dependencies","capabilities","allowed_paths","allowed_effects","trace_links","framework_reuse"): object.__setattr__(self,n,_list(getattr(self,n)))
    def to_dict(self): return {k:wire(getattr(self,k)) for k in ("logical_key","objective","inputs","outputs","dependencies","capabilities","allowed_paths","allowed_effects","trace_links","framework_reuse")}
@dataclass(frozen=True)
class AcceptedWorkItem:
    logical_key:str; controller_id:LogicalId; content_revision:RevisionId; content_digest:TypedDigest
    def __post_init__(self):
        if type(self.logical_key) is not str or not isinstance(self.controller_id,LogicalId) or not isinstance(self.content_revision,RevisionId) or not isinstance(self.content_digest,TypedDigest): raise ModelError("malformed-record")
@dataclass(frozen=True)
class ControllerIdAssignment:
    logical_key:str; controller_id:LogicalId
    def __post_init__(self):
        if type(self.logical_key) is not str or not isinstance(self.controller_id,LogicalId): raise ModelError("malformed-record")
def _rid(v):
    try:return RevisionId.parse(v)
    except Exception: raise ModelError("malformed-record") from None
@dataclass(frozen=True)
class ModelEnvelope:
    schema_version:int; model_kind:str; model_id:LogicalId; revision_id:RevisionId; content_digest:TypedDigest; status:str; parents:tuple; intent_ref:str|None; source_refs:tuple; decision_refs:tuple; policy_refs:tuple; capability_refs:tuple; assumptions:tuple; unknowns:tuple; constraints:tuple; non_goals:tuple; risks:tuple; evidence_requirements:tuple; creation_metadata:object; base_metadata:object; payload:Payload
    def __post_init__(self):
        if self.schema_version != 1 or self.model_kind not in MODEL_KINDS: raise ModelError("invalid-model-kind")
        if not isinstance(self.model_id,LogicalId) or not isinstance(self.revision_id,RevisionId) or not isinstance(self.content_digest,TypedDigest): raise ModelError("invalid-model-identity")
        if self.model_id.kind != self.model_kind or self.revision_id.kind != self.model_kind or self.model_id.namespace != self.revision_id.namespace: raise ModelError("invalid-model-identity")
        if not isinstance(self.payload,Payload) or self.payload.KIND != self.model_kind: raise ModelError("model-payload-kind-mismatch")
        if self.status not in ("proposed","accepted","superseded","rejected"): raise ModelError("malformed-record")
        for n in ("parents","source_refs","decision_refs","policy_refs","capability_refs","assumptions","unknowns","constraints","non_goals","risks","evidence_requirements") : object.__setattr__(self,n,_list(getattr(self,n)))
        try:
            expected=revision_for(self.model_id.namespace,self.model_kind,self.material()); digest=TypedDigest.for_value("paf:model-content",self.material())
        except Exception: raise ModelError("malformed-record") from None
        if expected != self.revision_id: raise ModelError("model-revision-mismatch")
        if digest != self.content_digest: raise ModelError("model-digest-mismatch")
    def material(self): return {"schema_version":self.schema_version,"model_kind":self.model_kind,"model_id":str(self.model_id),"status":self.status,"parents":wire(self.parents),"intent_ref":self.intent_ref,"source_refs":wire(self.source_refs),"decision_refs":wire(self.decision_refs),"policy_refs":wire(self.policy_refs),"capability_refs":wire(self.capability_refs),"assumptions":wire(self.assumptions),"unknowns":wire(self.unknowns),"constraints":wire(self.constraints),"non_goals":wire(self.non_goals),"risks":wire(self.risks),"evidence_requirements":wire(self.evidence_requirements),"creation_metadata":wire(self.creation_metadata),"base_metadata":wire(self.base_metadata),"payload":self.payload.to_dict()}
    @classmethod
    def create(cls, *, model_id, status, payload, creation_metadata, base_metadata, **common):
        kind=payload.KIND; material={"schema_version":1,"model_kind":kind,"model_id":str(model_id),"status":status,"parents":list(common.get("parents",())),"intent_ref":common.get("intent_ref"),"source_refs":list(common.get("source_refs",())),"decision_refs":list(common.get("decision_refs",())),"policy_refs":list(common.get("policy_refs",())),"capability_refs":list(common.get("capability_refs",())),"assumptions":list(common.get("assumptions",())),"unknowns":list(common.get("unknowns",())),"constraints":list(common.get("constraints",())),"non_goals":list(common.get("non_goals",())),"risks":list(common.get("risks",())),"evidence_requirements":list(common.get("evidence_requirements",())),"creation_metadata":creation_metadata,"base_metadata":base_metadata,"payload":payload.to_dict()}
        return cls(1,kind,model_id,revision_for(model_id.namespace,kind,material),TypedDigest.for_value("paf:model-content",material),status,tuple(material["parents"]),material["intent_ref"],tuple(material["source_refs"]),tuple(material["decision_refs"]),tuple(material["policy_refs"]),tuple(material["capability_refs"]),tuple(material["assumptions"]),tuple(material["unknowns"]),tuple(material["constraints"]),tuple(material["non_goals"]),tuple(material["risks"]),tuple(material["evidence_requirements"]),creation_metadata,base_metadata,payload)
    def to_dict(self):
        d=self.material(); d.update(revision_id=str(self.revision_id),content_digest=str(self.content_digest)); return d
    @classmethod
    def from_dict(cls,d):
        fields=("schema_version","model_kind","model_id","revision_id","content_digest","status","parents","intent_ref","source_refs","decision_refs","policy_refs","capability_refs","assumptions","unknowns","constraints","non_goals","risks","evidence_requirements","creation_metadata","base_metadata","payload"); exact(d,fields,ModelError)
        try:
            kind=d["model_kind"]; p=_PAYLOADS[kind].from_dict(d["payload"]); tuples={x:tuple(d[x]) for x in fields if x.endswith("refs") or x in ("parents","assumptions","unknowns","constraints","non_goals","risks","evidence_requirements")}
            return cls(d["schema_version"],kind,LogicalId.parse(d["model_id"]),_rid(d["revision_id"]),TypedDigest.parse(d["content_digest"]),d["status"],tuples["parents"],d["intent_ref"],tuples["source_refs"],tuples["decision_refs"],tuples["policy_refs"],tuples["capability_refs"],tuples["assumptions"],tuples["unknowns"],tuples["constraints"],tuples["non_goals"],tuples["risks"],tuples["evidence_requirements"],d["creation_metadata"],d["base_metadata"],p)
        except ModelError: raise
        except Exception: raise ModelError("malformed-record") from None
