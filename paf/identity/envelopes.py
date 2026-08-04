from dataclasses import dataclass
from .canonical import canonical_bytes
from .digest import TypedDigest
from .errors import ExtensionError,MigrationError
@dataclass(frozen=True)
class ExtensionEnvelope:
 name:str; required:bool; preservable:bool; payload:object
 def __post_init__(self): canonical_bytes(self.payload)
 @classmethod
 def from_dict(cls,d):
  if not isinstance(d,dict) or set(d)!={'name','required','preservable','payload'}: raise ExtensionError('unexpected-envelope-field')
  if type(d['required']) is not bool or type(d['preservable']) is not bool: raise ExtensionError('malformed-extension')
  return cls(**d)
@dataclass(frozen=True)
class MigrationEnvelope:
 source:object; target:object; source_digest:TypedDigest; operation:str; lossless:bool; extensions:tuple=()
 def __post_init__(self):
  if self.lossless is not True: raise MigrationError('lossy-migration')
  if not isinstance(self.source_digest,TypedDigest): raise MigrationError('malformed-migration')
  canonical_bytes(self.source); canonical_bytes(self.target)
  self.source_digest.verify(self.source)
@dataclass(frozen=True)
class NegotiationOffer:
 namespace:object; schema:str; version:object; profile:str='paf-json-v1'; extensions:tuple=()
@dataclass(frozen=True,order=True)
class NegotiationResult:
 status:str; code:str='ok'; migration_operation:str|None=None
