"""Pure non-authoritative repository-state projection."""
from dataclasses import dataclass
from paf.identity import TypedDigest, canonical_bytes
from paf.kernel.errors import ProjectionError
from paf.kernel.records import wire
@dataclass(frozen=True)
class RepositoryStateProjection:
    projection_id:str; exact_base:str; accepted_models:tuple; completed_work:object=None; active_work:object=None; history:object=None; defects:object=None; capability_gaps:object=None; adapters:object=None; source_refs:tuple=()
    def __post_init__(self):
        if type(self.projection_id) is not str or type(self.exact_base) is not str: raise ProjectionError("malformed-record")
        for n in ("accepted_models","source_refs"):
            if type(getattr(self,n)) not in (tuple,list): raise ProjectionError("malformed-record")
            object.__setattr__(self,n,tuple(getattr(self,n)))
        for n in ("completed_work","active_work","history","defects","capability_gaps","adapters"):
            v=getattr(self,n)
            if type(v) is list: object.__setattr__(self,n,tuple(v))
        try: canonical_bytes(self.to_dict())
        except Exception: raise ProjectionError("malformed-record") from None
    @property
    def revision(self): return str(TypedDigest.for_value("paf:repository-projection",self.to_dict()))
    def to_dict(self): return {x:wire(getattr(self,x)) for x in self.__dataclass_fields__}
