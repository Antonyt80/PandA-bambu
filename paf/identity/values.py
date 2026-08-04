from dataclasses import dataclass
import re
from .errors import IdentitySyntaxError
_NS=re.compile(r'[a-z](?:[a-z0-9-]*[a-z0-9])?(?:\.[a-z](?:[a-z0-9-]*[a-z0-9])?)*\Z')
_KIND=re.compile(r'[a-z](?:[a-z0-9-]*[a-z0-9])?\Z')
_LOCAL=re.compile(r'[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?\Z')
@dataclass(frozen=True, order=True)
class Namespace:
 value:str
 def __post_init__(self):
  if not isinstance(self.value,str) or not _NS.fullmatch(self.value): raise IdentitySyntaxError('invalid-namespace')
 def __str__(self): return self.value
 @classmethod
 def parse(cls,s): return cls(s)
@dataclass(frozen=True, order=True)
class SchemaVersion:
 major:int; minor:int
 def __post_init__(self):
  if type(self.major) is not int or type(self.minor) is not int or self.major<0 or self.minor<0: raise IdentitySyntaxError('invalid-schema-version')
 def __str__(self): return f'{self.major}.{self.minor}'
 @classmethod
 def parse(cls,s):
  if not isinstance(s,str) or not re.fullmatch(r'(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)',s): raise IdentitySyntaxError('invalid-schema-version')
  a,b=s.split('.'); return cls(int(a),int(b))
def _component(x): return isinstance(x,str) and _KIND.fullmatch(x)
def _local(x): return isinstance(x,str) and _LOCAL.fullmatch(x)
@dataclass(frozen=True, order=True)
class LogicalId:
 namespace:Namespace; kind:str; name:str
 def __post_init__(self):
  if not isinstance(self.namespace,Namespace) or not _component(self.kind) or not _local(self.name): raise IdentitySyntaxError('invalid-logical-id')
 def __str__(self): return f'lid1:{self.namespace}:{self.kind}:{self.name}'
 @classmethod
 def parse(cls,s):
  p=s.split(':') if isinstance(s,str) else []
  if len(p)!=4 or p[0]!='lid1': raise IdentitySyntaxError('invalid-logical-id')
  return cls(Namespace(p[1]),p[2],p[3])
@dataclass(frozen=True, order=True)
class RevisionId:
 namespace:Namespace; kind:str; profile:str; algorithm:str; digest:bytes
 def __post_init__(self):
  if not isinstance(self.namespace,Namespace) or not _component(self.kind) or self.profile!='paf-json-v1' or self.algorithm!='sha256' or type(self.digest) is not bytes or len(self.digest)!=32: raise IdentitySyntaxError('invalid-revision-id')
 def __str__(self): return f'rid1:{self.namespace}:{self.kind}:{self.profile}:{self.algorithm}:{self.digest.hex()}'
 @classmethod
 def parse(cls,s):
  p=s.split(':') if isinstance(s,str) else []
  if len(p)!=6 or p[:1]!=['rid1'] or not re.fullmatch('[0-9a-f]{64}',p[-1]): raise IdentitySyntaxError('invalid-revision-id')
  return cls(Namespace(p[1]),p[2],p[3],p[4],bytes.fromhex(p[5]))
@dataclass(frozen=True, order=True)
class BinaryValue:
 data:bytes
 def __post_init__(self):
  if type(self.data) is not bytes: raise IdentitySyntaxError('invalid-binary')
