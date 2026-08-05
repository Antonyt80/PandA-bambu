"""PAF-DEC-003 typed SHA-256 digests and revision derivation."""
from dataclasses import dataclass
import hashlib, hmac, re

from .canonical import canonical_bytes
from .errors import DigestError
from .values import ALGORITHM, PROFILE, Namespace, RevisionId, valid_kind

MAGIC = b"PAF-DIGEST-1"
_DOMAIN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/-]*\Z")


def _frame(value):
    try:
        raw = value if type(value) is bytes else value.encode("ascii")
        if len(raw) > 0xffffffffffffffff: raise OverflowError
        return len(raw).to_bytes(8, "big") + raw
    except (AttributeError, UnicodeEncodeError, OverflowError):
        raise DigestError("invalid-typed-digest") from None


def _valid_domain(domain): return type(domain) is str and bool(_DOMAIN.fullmatch(domain))


def _hash(domain, profile, data):
    if not _valid_domain(domain) or profile != PROFILE or type(data) is not bytes: raise DigestError("invalid-typed-digest")
    return hashlib.sha256(MAGIC + _frame(b"sha256") + _frame(domain) + _frame(profile) + _frame(data)).digest()


@dataclass(frozen=True, order=True)
class TypedDigest:
    profile: str
    domain: str
    algorithm: str
    digest: bytes

    def __post_init__(self):
        if self.profile != PROFILE or not _valid_domain(self.domain) or self.algorithm != ALGORITHM or type(self.digest) is not bytes or len(self.digest) != 32:
            raise DigestError("invalid-typed-digest")

    def __str__(self): return f"td1:{self.profile}:{self.domain}:{self.algorithm}:{self.digest.hex()}"

    @classmethod
    def parse(cls, value):
        try:
            if type(value) is not str: raise ValueError
            left, algorithm, hexadecimal = value.rsplit(":", 2)
            prefix, profile, domain = left.split(":", 2)
            if prefix != "td1" or not re.fullmatch(r"[0-9a-f]{64}", hexadecimal): raise ValueError
            return cls(profile, domain, algorithm, bytes.fromhex(hexadecimal))
        except (ValueError, DigestError):
            raise DigestError("invalid-typed-digest") from None

    @classmethod
    def for_value(cls, domain, value, profile=PROFILE):
        if profile != PROFILE: raise DigestError("unknown-profile")
        if not _valid_domain(domain): raise DigestError("invalid-typed-digest")
        return cls(profile, domain, ALGORITHM, _hash(domain, profile, canonical_bytes(value)))

    def verify(self, value):
        if not hmac.compare_digest(self.digest, _hash(self.domain, self.profile, canonical_bytes(value))):
            raise DigestError("digest-mismatch")
        return True


def revision_for(namespace, kind, value):
    try:
        namespace = Namespace(namespace) if type(namespace) is str else namespace
        if not isinstance(namespace, Namespace) or not valid_kind(kind): raise ValueError
        digest = TypedDigest.for_value(f"revision:{namespace}:{kind}", value)
        return RevisionId(namespace, kind, digest.profile, digest.algorithm, digest.digest)
    except (ValueError, DigestError):
        raise DigestError("invalid-revision-id") from None


def verify_revision(revision, value):
    if not isinstance(revision, RevisionId): raise DigestError("invalid-revision-id")
    TypedDigest(revision.profile, f"revision:{revision.namespace}:{revision.kind}", revision.algorithm, revision.digest).verify(value)
    return True