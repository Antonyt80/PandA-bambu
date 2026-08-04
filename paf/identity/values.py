"""Alias-free value types used by the PAF R1 identity wire format."""
from dataclasses import dataclass
import re

from .errors import IdentitySyntaxError

PROFILE = "paf-json-v1"
ALGORITHM = "sha256"
_NS = re.compile(r"[a-z](?:[a-z0-9-]*[a-z0-9])?(?:\.[a-z](?:[a-z0-9-]*[a-z0-9])?)*\Z")
_KIND = re.compile(r"[a-z](?:[a-z0-9-]*[a-z0-9])?\Z")
_LOCAL = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?\Z")


@dataclass(frozen=True, order=True)
class Namespace:
    value: str

    def __post_init__(self):
        if type(self.value) is not str or not _NS.fullmatch(self.value):
            raise IdentitySyntaxError("invalid-namespace")

    def __str__(self): return self.value

    @classmethod
    def parse(cls, value): return cls(value)


@dataclass(frozen=True, order=True)
class SchemaVersion:
    major: int
    minor: int

    def __post_init__(self):
        if type(self.major) is not int or type(self.minor) is not int or self.major < 0 or self.minor < 0:
            raise IdentitySyntaxError("invalid-schema-version")

    def __str__(self): return f"{self.major}.{self.minor}"

    @classmethod
    def parse(cls, value):
        if type(value) is not str or not re.fullmatch(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)", value):
            raise IdentitySyntaxError("invalid-schema-version")
        major, minor = value.split(".")
        return cls(int(major), int(minor))


def valid_kind(value): return type(value) is str and bool(_KIND.fullmatch(value))
def valid_local(value): return type(value) is str and bool(_LOCAL.fullmatch(value))


@dataclass(frozen=True, order=True)
class LogicalId:
    namespace: Namespace
    kind: str
    name: str

    def __post_init__(self):
        if not isinstance(self.namespace, Namespace) or not valid_kind(self.kind) or not valid_local(self.name):
            raise IdentitySyntaxError("invalid-logical-id")

    def __str__(self): return f"lid1:{self.namespace}:{self.kind}:{self.name}"

    @classmethod
    def parse(cls, value):
        try:
            parts = value.split(":") if type(value) is str else []
            if len(parts) != 4 or parts[0] != "lid1": raise ValueError
            return cls(Namespace(parts[1]), parts[2], parts[3])
        except (ValueError, IdentitySyntaxError):
            raise IdentitySyntaxError("invalid-logical-id") from None


@dataclass(frozen=True, order=True)
class RevisionId:
    namespace: Namespace
    kind: str
    profile: str
    algorithm: str
    digest: bytes

    def __post_init__(self):
        if (not isinstance(self.namespace, Namespace) or not valid_kind(self.kind) or self.profile != PROFILE or
                self.algorithm != ALGORITHM or type(self.digest) is not bytes or len(self.digest) != 32):
            raise IdentitySyntaxError("invalid-revision-id")

    def __str__(self): return f"rid1:{self.namespace}:{self.kind}:{self.profile}:{self.algorithm}:{self.digest.hex()}"

    @classmethod
    def parse(cls, value):
        try:
            parts = value.split(":") if type(value) is str else []
            if len(parts) != 6 or parts[0] != "rid1" or not re.fullmatch(r"[0-9a-f]{64}", parts[5]): raise ValueError
            return cls(Namespace(parts[1]), parts[2], parts[3], parts[4], bytes.fromhex(parts[5]))
        except (ValueError, IdentitySyntaxError):
            raise IdentitySyntaxError("invalid-revision-id") from None


@dataclass(frozen=True, order=True)
class BinaryValue:
    data: bytes

    def __post_init__(self):
        if type(self.data) is not bytes: raise IdentitySyntaxError("invalid-binary")