"""Strict wire envelopes; parsing does not execute a migration."""
from dataclasses import dataclass
from .canonical import canonical_bytes
from .digest import TypedDigest
from .errors import ExtensionError,MigrationError
from .values import PROFILE,Namespace,SchemaVersion,valid_kind
def _exact(data,fields,error):
    if type(data) is not dict or set(data)!=set(fields):raise error("unexpected-envelope-field")
@dataclass(frozen=True)
class ExtensionEnvelope:
    name:str; required:bool; preservable:bool; payload:object
    def __post_init__(self):
        if not valid_kind(self.name) or type(self.required) is not bool or type(self.preservable) is not bool:raise ExtensionError("malformed-extension")
        canonical_bytes(self.payload)
    @classmethod
    def from_dict(cls,data):
        _exact(data,("name","required","preservable","payload"),ExtensionError)
        try:return cls(**data)
        except ExtensionError:raise
        except Exception:raise ExtensionError("malformed-extension") from None
    def to_dict(self):return {"name":self.name,"required":self.required,"preservable":self.preservable,"payload":self.payload}
@dataclass(frozen=True)
class NegotiationOffer:
    namespace:Namespace; schema:str; version:SchemaVersion; profile:str=PROFILE; extensions:tuple=()
    def __post_init__(self):
        if (not isinstance(self.namespace,Namespace) or not valid_kind(self.schema) or
                not isinstance(self.version,SchemaVersion) or type(self.profile) is not str or
                not self.profile or type(self.extensions) is not tuple or
                not all(isinstance(x,ExtensionEnvelope) for x in self.extensions)):
            raise ExtensionError("malformed-offer")
        if len({extension.name for extension in self.extensions}) != len(self.extensions):
            raise ExtensionError("duplicate-extension")
    @classmethod
    def from_dict(cls,data):
        _exact(data,("namespace","schema","version","profile","extensions"),ExtensionError)
        try:
            if type(data["extensions"]) is not list:raise ValueError
            return cls(Namespace(data["namespace"]),data["schema"],SchemaVersion.parse(data["version"]),data["profile"],tuple(ExtensionEnvelope.from_dict(x) for x in data["extensions"]))
        except (ValueError,ExtensionError):raise ExtensionError("malformed-offer") from None
@dataclass(frozen=True,order=True)
class NegotiationResult:
    status:str; code:str="ok"; migration_operation:str|None=None
    def __post_init__(self):
        if self.status == "exact-compatible" and self.code == "ok" and self.migration_operation is None:return
        if self.status == "migration-required" and self.code == "migration-required" and valid_kind(self.migration_operation):return
        raise ExtensionError("malformed-negotiation-result")
@dataclass(frozen=True)
class MigrationEnvelope:
    source:object; target:object; source_digest:TypedDigest; operation:str; lossless:bool; extensions:tuple=()
    def __post_init__(self):
        if self.lossless is not True:raise MigrationError("lossy-migration")
        if not isinstance(self.source_digest,TypedDigest) or not valid_kind(self.operation) or type(self.extensions) is not tuple or not all(isinstance(x,ExtensionEnvelope) for x in self.extensions):raise MigrationError("malformed-migration")
        if len({extension.name for extension in self.extensions}) != len(self.extensions):raise MigrationError("malformed-migration")
        try:canonical_bytes(self.source); canonical_bytes(self.target); self.source_digest.verify(self.source)
        except Exception as error:
            if getattr(error,"code",None)=="digest-mismatch":raise MigrationError("digest-mismatch") from None
            raise MigrationError("malformed-migration") from None
    @classmethod
    def from_dict(cls,data):
        _exact(data,("source","target","source_digest","operation","lossless","extensions"),MigrationError)
        try:
            if type(data["source_digest"]) is not str or type(data["extensions"]) is not list:raise ValueError
            return cls(data["source"],data["target"],TypedDigest.parse(data["source_digest"]),data["operation"],data["lossless"],tuple(ExtensionEnvelope.from_dict(x) for x in data["extensions"]))
        except MigrationError:raise
        except Exception as error:
            if getattr(error,"code",None)=="digest-mismatch":raise MigrationError("digest-mismatch") from None
            raise MigrationError("malformed-migration") from None
    def verify_registered(self,registry,source_key,target_key):
        if not getattr(registry,"frozen",False):raise MigrationError("registry-not-frozen")
        matches=[x for x in registry.migrations if x.source==source_key and x.target==target_key and x.operation==self.operation and x.lossless]
        if not matches:raise MigrationError("unknown-migration")
        if len(matches)!=1:raise MigrationError("ambiguous-migration")
        return True