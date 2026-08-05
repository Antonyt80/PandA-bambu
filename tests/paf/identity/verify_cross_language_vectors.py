"""Offline agreement check for the independent Python and Node vector readers."""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
VECTORS = ROOT / "tests/paf/identity/vectors/paf_identity_v1.json"
REQUIRED_DECISIONS = {f"PAF-DEC-00{i}" for i in range(1, 6)}
REQUIRED_CANONICAL = {
    "PF-IDENTITY-001",
    "PF-IDENTITY-NULL",
    "PF-IDENTITY-SAFE-BOUNDARIES",
    "PF-IDENTITY-SCALAR-ORDER",
}
REQUIRED_DIGESTS = {"PF-DIGEST-001", "PF-DIGEST-REVISION-DOMAIN"}
REQUIRED_JSON_TEXT = {"PF-IDENTITY-BINARY"}
REQUIRED_REJECTIONS = {f"NF-IDENTITY-00{i}" for i in range(1, 7)}

sys.path.insert(0, str(ROOT))
from paf.identity import IdentityError, TypedDigest, canonical_bytes, canonicalize_json_text


def require_ids(data, collection, expected):
    vectors = data.get(collection)
    if not isinstance(vectors, list) or {vector.get("id") for vector in vectors} != expected:
        raise SystemExit(f"incomplete {collection} vector coverage")


def main():
    data = json.loads(VECTORS.read_text(encoding="utf-8"))
    if data.get("vector_schema") != "paf-identity-v1" or set(data.get("decisions", [])) != REQUIRED_DECISIONS:
        raise SystemExit("incomplete vector coverage")
    require_ids(data, "canonical", REQUIRED_CANONICAL)
    require_ids(data, "digests", REQUIRED_DIGESTS)
    require_ids(data, "json_text", REQUIRED_JSON_TEXT)
    require_ids(data, "rejections", REQUIRED_REJECTIONS)

    for vector in data["canonical"]:
        if canonical_bytes(vector["value"]).hex() != vector["hex"]:
            raise SystemExit("python canonical mismatch: " + vector["id"])
    for vector in data["digests"]:
        if str(TypedDigest.for_value(vector["domain"], vector["value"])) != vector["wire"]:
            raise SystemExit("python digest mismatch: " + vector["id"])
    for vector in data["json_text"]:
        if canonicalize_json_text(vector["input"]).hex() != vector["hex"]:
            raise SystemExit("python JSON text mismatch: " + vector["id"])
    for vector in data["rejections"]:
        try:
            operation = canonicalize_json_text if vector["kind"] == "json-text" else canonical_bytes
            operation(vector["input"])
        except IdentityError as error:
            if error.code != vector["code"]:
                raise SystemExit("python rejection mismatch: " + vector["id"])
        else:
            raise SystemExit("python rejection accepted: " + vector["id"])

    node = shutil.which("node")
    if not node:
        raise SystemExit("node unavailable")
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PAF_IDENTITY_NODE_ONLY="1")
    result = subprocess.run(
        [node, str(ROOT / "tests/paf/identity/verify_vectors.mjs")],
        cwd=ROOT,
        text=True,
        capture_output=True,
        env=env,
    )
    if result.returncode:
        raise SystemExit(result.stdout + result.stderr)
    print("cross-language vectors: ok")


if __name__ == "__main__":
    main()
