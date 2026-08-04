from dataclasses import dataclass,field
from .errors import RegistryError,NegotiationError
from .values import Namespace,SchemaVersion
@dataclass(frozen=True)
class SchemaKey: namespace:Namespace; schema:str; version:SchemaVersion
@dataclass
class IdentityRegistry:
 namespaces:set=field(default_factory=set); profiles:set=field(default_factory=lambda:{'paf-json-v1'}); schemas:set=field(default_factory=set); extensions:dict=field(default_factory=dict); compatibility:set=field(default_factory=set); migrations:set=field(default_factory=set); frozen:bool=False
 def _open(self):
  if self.frozen: raise RegistryError('registry-frozen')
 def register_namespace(self,n):
  self._open(); n=Namespace(n) if isinstance(n,str) else n
  if n in self.namespaces: raise RegistryError('duplicate-registration')
  self.namespaces.add(n); return self
 def register_schema(self,n,s,v):
  self._open(); k=SchemaKey(Namespace(n) if isinstance(n,str) else n,s,SchemaVersion.parse(v) if isinstance(v,str) else v)
  if k in self.schemas: raise RegistryError('duplicate-registration')
  self.schemas.add(k); return self
 def register_extension(self,name,preservable=False):
  self._open()
  if name in self.extensions: raise RegistryError('duplicate-registration')
  self.extensions[name]=bool(preservable); return self
 def add_migration(self,source,target,operation):
  self._open(); edge=(source,target,operation)
  if edge in self.migrations: raise RegistryError('duplicate-registration')
  self.migrations.add(edge); return self
 def freeze(self): self.frozen=True; return self
