from .values import Namespace,SchemaVersion
from .registry import SchemaKey
from .envelopes import NegotiationResult
from .errors import NegotiationError

def negotiate(registry,offer):
 n=Namespace(offer.namespace) if isinstance(offer.namespace,str) else offer.namespace
 v=SchemaVersion.parse(offer.version) if isinstance(offer.version,str) else offer.version
 if n not in registry.namespaces: raise NegotiationError('unknown-namespace')
 if offer.profile not in registry.profiles: raise NegotiationError('unknown-profile')
 key=SchemaKey(n,offer.schema,v)
 for ext in offer.extensions:
  if ext.name not in registry.extensions:
   if ext.required: raise NegotiationError('unknown-extension')
   if not (ext.preservable and registry.extensions.get(ext.name,False)): raise NegotiationError('unknown-extension')
 if key in registry.schemas:return NegotiationResult('exact-compatible')
 candidates=sorted((op for a,b,op in registry.migrations if b==key),key=str)
 if len(candidates)==1:return NegotiationResult('migration-required','migration-required',candidates[0])
 if len(candidates)>1: raise NegotiationError('ambiguous-migration')
 if any(k.namespace==n and k.schema==offer.schema for k in registry.schemas): raise NegotiationError('unknown-version')
 raise NegotiationError('unknown-schema')
