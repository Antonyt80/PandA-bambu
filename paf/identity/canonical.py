import base64,json,math,unicodedata
from .values import BinaryValue
from .errors import CanonicalizationError
MIN=-9007199254740991; MAX=9007199254740991

def _string(s):
 if not isinstance(s,str) or any(0xD800<=ord(c)<=0xDFFF for c in s): raise CanonicalizationError('invalid-unicode-scalar')
 return unicodedata.normalize('NFC',s)
def _quote(s): return json.dumps(_string(s),ensure_ascii=False,separators=(',',':'))
def _encode(v):
 if v is None:return 'null'
 if type(v) is bool:return 'true' if v else 'false'
 if type(v) is int:
  if not MIN<=v<=MAX: raise CanonicalizationError('integer-out-of-range')
  return str(v)
 if isinstance(v,float): raise CanonicalizationError('unsupported-semantic-type')
 if isinstance(v,str): return _quote(v)
 if isinstance(v,BinaryValue): return '{"$paf-binary":'+_quote(base64.urlsafe_b64encode(v.data).decode().rstrip('='))+'}'
 if isinstance(v,list): return '['+','.join(_encode(x) for x in v)+']'
 if isinstance(v,dict):
  pairs=[]; seen=set()
  for k,x in v.items():
   nk=_string(k)
   if nk in seen: raise CanonicalizationError('non-nfc-collision')
   seen.add(nk); pairs.append((nk,x))
  if set(v)=={'$paf-binary'}: raise CanonicalizationError('reserved-binary-tag')
  return '{'+','.join(_quote(k)+':'+_encode(x) for k,x in sorted(pairs,key=lambda p:tuple(map(ord,p[0]))))+'}'
 raise CanonicalizationError('unsupported-semantic-type')
def canonical_bytes(value): return _encode(value).encode('utf-8')
def _pairs(pairs):
 d={}
 for k,v in pairs:
  if k in d: raise CanonicalizationError('duplicate-object-key')
  d[k]=v
 return d
def canonicalize_json_text(text):
 if isinstance(text,bytes):
  if text.startswith(b'\xef\xbb\xbf'): raise CanonicalizationError('invalid-json-text')
  try:text=text.decode('utf-8')
  except UnicodeDecodeError: raise CanonicalizationError('invalid-json-text')
 if not isinstance(text,str): raise CanonicalizationError('invalid-json-text')
 try: v=json.loads(text,object_pairs_hook=_pairs,parse_constant=lambda _:(_ for _ in ()).throw(CanonicalizationError('unsupported-semantic-type')),parse_float=lambda _:(_ for _ in ()).throw(CanonicalizationError('unsupported-semantic-type')))
 except CanonicalizationError: raise
 except (ValueError,TypeError): raise CanonicalizationError('invalid-json-text')
 return canonical_bytes(v)
