from dataclasses import dataclass
import hashlib,hmac,re
from .canonical import canonical_bytes
from .errors import DigestError
from .values import Namespace,RevisionId
MAGIC=b'PAF-DIGEST-1'
def _frame(x):
 if not isinstance(x,bytes): x=x.encode('ascii')
 return len(x).to_bytes(8,'big')+x
def _hash(domain,profile,data): return hashlib.sha256(MAGIC+_frame(b'sha256')+_frame(domain)+_frame(profile)+_frame(data)).digest()
@dataclass(frozen=True, order=True)
class TypedDigest:
 profile:str; domain:str; algorithm:str; digest:bytes
 def __post_init__(self):
  if self.profile!='paf-json-v1' or not isinstance(self.domain,str) or not self.domain or self.algorithm!='sha256' or type(self.digest) is not bytes or len(self.digest)!=32: raise DigestError('invalid-typed-digest')
 def __str__(self): return f'td1:{self.profile}:{self.domain}:{self.algorithm}:{self.digest.hex()}'
 @classmethod
 def parse(cls,s):
  p=s.split(':') if isinstance(s,str) else []
  if len(p)!=5 or p[0]!='td1' or not re.fullmatch('[0-9a-f]{64}',p[-1]): raise DigestError('invalid-typed-digest')
  return cls(p[1],p[2],p[3],bytes.fromhex(p[4]))
 @classmethod
 def for_value(cls,domain,value,profile='paf-json-v1'):
  if profile!='paf-json-v1': raise DigestError('unknown-profile')
  return cls(profile,domain,'sha256',_hash(domain,profile,canonical_bytes(value)))
 def verify(self,value):
  if not hmac.compare_digest(self.digest,_hash(self.domain,self.profile,canonical_bytes(value))): raise DigestError('digest-mismatch')
  return True
def revision_for(namespace,kind,value):
 if not isinstance(namespace,Namespace): namespace=Namespace(namespace)
 domain=f'revision:{namespace}:{kind}'
 d=TypedDigest.for_value(domain,value)
 return RevisionId(namespace,kind,d.profile,d.algorithm,d.digest)
