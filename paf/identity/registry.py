"""Explicit, frozen registrations for identity negotiation."""
from dataclasses import dataclass,field
from types import MappingProxyType
from .errors import RegistryError
from .values import PROFILE,Namespace,SchemaVersion,valid_kind
@dataclass(frozen=True,order=True)
class SchemaKey:
    namespace:Namespace; schema:str; version:SchemaVersion; profile:str=PROFILE
    def __post_init__(self):
        if not isinstance(self.namespace,Namespace) or not valid_kind(self.schema) or not isinstance(self.version,SchemaVersion) or self.profile!=PROFILE: raise RegistryError("invalid-registration")
@dataclass(frozen=True,order=True)
class MigrationRegistration:
    source:SchemaKey; target:SchemaKey; operation:str; lossless:bool=True
    def __post_init__(self):
        if not isinstance(self.source,SchemaKey) or not isinstance(self.target,SchemaKey) or not valid_kind(self.operation) or self.lossless is not True: raise RegistryError("invalid-registration")
@dataclass
class IdentityRegistry:
    namespaces:set=field(default_factory=set); profiles:set=field(default_factory=set); schemas:set=field(default_factory=set); extensions:dict=field(default_factory=dict); migrations:set=field(default_factory=set); preserve_unknown_optional_extensions:bool=False; frozen:bool=False
    def _open(self):
        if self.frozen: raise RegistryError("registry-frozen")
    def register_namespace(self,namespace):
        self._open()
        try:namespace=Namespace(namespace) if type(namespace) is str else namespace
        except Exception:raise RegistryError("invalid-registration") from None
        if not isinstance(namespace,Namespace):raise RegistryError("invalid-registration")
        if namespace in self.namespaces:raise RegistryError("duplicate-registration")
        self.namespaces.add(namespace); return self
    def register_profile(self,profile):
        self._open()
        if profile!=PROFILE:raise RegistryError("invalid-registration")
        if profile in self.profiles:raise RegistryError("duplicate-registration")
        self.profiles.add(profile); return self
    def register_schema(self,namespace,schema,version,profile=PROFILE):
        self._open()
        try:
            namespace=Namespace(namespace) if type(namespace) is str else namespace; version=SchemaVersion.parse(version) if type(version) is str else version; key=SchemaKey(namespace,schema,version,profile)
        except Exception:raise RegistryError("invalid-registration") from None
        if namespace not in self.namespaces or profile not in self.profiles:raise RegistryError("invalid-registration")
        if key in self.schemas:raise RegistryError("duplicate-registration")
        self.schemas.add(key); return self
    def register_extension(self,name,preservable=False):
        self._open()
        if not valid_kind(name) or type(preservable) is not bool:raise RegistryError("invalid-registration")
        if name in self.extensions:raise RegistryError("duplicate-registration")
        self.extensions[name]=preservable; return self
    def set_unknown_optional_extension_preservation(self,supported):
        self._open()
        if type(supported) is not bool:raise RegistryError("invalid-registration")
        self.preserve_unknown_optional_extensions=supported; return self
    def add_migration(self,source,target,operation,lossless=True):
        self._open()
        try:registration=MigrationRegistration(source,target,operation,lossless)
        except Exception:raise RegistryError("invalid-registration") from None
        if registration.source.namespace not in self.namespaces or registration.source.profile not in self.profiles or registration.target not in self.schemas:raise RegistryError("invalid-registration")
        if registration in self.migrations:raise RegistryError("duplicate-registration")
        self.migrations.add(registration); return self
    def freeze(self):
        self._open()
        if not self.profiles:raise RegistryError("invalid-registration")
        self.namespaces=frozenset(self.namespaces); self.profiles=frozenset(self.profiles); self.schemas=frozenset(self.schemas); self.extensions=MappingProxyType(dict(self.extensions)); self.migrations=frozenset(self.migrations); self.frozen=True
        return self