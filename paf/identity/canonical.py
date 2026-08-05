"""Deterministic restricted paf-json-v1 semantic encoding."""
import base64, json, unicodedata
from .errors import CanonicalizationError
from .values import BinaryValue
MIN=-9007199254740991; MAX=9007199254740991; _TAG="$paf-binary"

def _string(value):
    if type(value) is not str or any(0xD800<=ord(c)<=0xDFFF for c in value): raise CanonicalizationError("invalid-unicode-scalar")
    return unicodedata.normalize("NFC",value)
def _quote(value): return json.dumps(_string(value),ensure_ascii=False,separators=(",",":"))
def _binary_text(value): return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")
def _decode_binary(value):
    if type(value) is not str or "=" in value or any(c not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_" for c in value): raise CanonicalizationError("invalid-binary")
    try: raw=base64.urlsafe_b64decode(value+"="*((4-len(value)%4)%4))
    except (ValueError,UnicodeError): raise CanonicalizationError("invalid-binary") from None
    if _binary_text(raw)!=value: raise CanonicalizationError("invalid-binary")
    return BinaryValue(raw)
def _encode(value,active):
    if value is None:return "null"
    if type(value) is bool:return "true" if value else "false"
    if type(value) is int:
        if not MIN<=value<=MAX: raise CanonicalizationError("integer-out-of-range")
        return str(value)
    if type(value) is float: raise CanonicalizationError("unsupported-semantic-type")
    if type(value) is str:return _quote(value)
    if isinstance(value,BinaryValue):return '{"$paf-binary":'+_quote(_binary_text(value.data))+"}"
    if isinstance(value,(list,dict)):
        marker=id(value)
        if marker in active: raise CanonicalizationError("cyclic-semantic-value")
        active.add(marker)
        try:
            if isinstance(value,list): return "["+",".join(_encode(x,active) for x in value)+"]"
            pairs=[]; seen=set()
            for key,child in value.items():
                normalized=_string(key)
                if normalized in seen: raise CanonicalizationError("non-nfc-collision")
                seen.add(normalized); pairs.append((normalized,child))
            if len(pairs)==1 and pairs[0][0]==_TAG: raise CanonicalizationError("reserved-binary-tag")
            return "{"+",".join(_quote(key)+":"+_encode(child,active) for key,child in sorted(pairs,key=lambda p:tuple(map(ord,p[0]))))+"}"
        finally: active.remove(marker)
    raise CanonicalizationError("unsupported-semantic-type")
def canonical_bytes(value):
    try:return _encode(value,set()).encode("utf-8")
    except RecursionError: raise CanonicalizationError("cyclic-semantic-value") from None
def _pairs(pairs):
    result={}; raw_keys=set(); normalized_keys=set()
    for key,value in pairs:
        if key in raw_keys: raise CanonicalizationError("duplicate-object-key")
        raw_keys.add(key)
        normalized=_string(key)
        if normalized in normalized_keys: raise CanonicalizationError("non-nfc-collision")
        normalized_keys.add(normalized)
        result[normalized]=value
    if set(result)=={_TAG}: return _decode_binary(result[_TAG])
    return result
def parse_json_text(text):
    if type(text) is bytes:
        if text.startswith(b"\xef\xbb\xbf"): raise CanonicalizationError("invalid-json-text")
        try:text=text.decode("utf-8")
        except UnicodeDecodeError: raise CanonicalizationError("invalid-json-text") from None
    if type(text) is not str or text.startswith("\ufeff"): raise CanonicalizationError("invalid-json-text")
    try:return json.loads(text,object_pairs_hook=_pairs,parse_constant=lambda _:(_ for _ in ()).throw(CanonicalizationError("unsupported-semantic-type")),parse_float=lambda _:(_ for _ in ()).throw(CanonicalizationError("unsupported-semantic-type")))
    except CanonicalizationError:raise
    except (ValueError,TypeError,RecursionError): raise CanonicalizationError("invalid-json-text") from None
def canonicalize_json_text(text): return canonical_bytes(parse_json_text(text))