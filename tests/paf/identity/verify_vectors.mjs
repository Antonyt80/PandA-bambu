import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

const PROFILE = "paf-json-v1";
const SCHEMA = "paf-identity-v1";
const REQUIRED_DECISIONS = new Set([
  "PAF-DEC-001",
  "PAF-DEC-002",
  "PAF-DEC-003",
  "PAF-DEC-004",
  "PAF-DEC-005",
]);
const REQUIRED_CANONICAL_IDS = new Set([
  "PF-IDENTITY-001",
  "PF-IDENTITY-NULL",
  "PF-IDENTITY-SAFE-BOUNDARIES",
  "PF-IDENTITY-SCALAR-ORDER",
]);
const REQUIRED_DIGEST_IDS = new Set([
  "PF-DIGEST-001",
  "PF-DIGEST-REVISION-DOMAIN",
]);
const REQUIRED_JSON_TEXT_IDS = new Set(["PF-IDENTITY-BINARY"]);
const REQUIRED_REJECTION_IDS = new Set([
  "NF-IDENTITY-001",
  "NF-IDENTITY-002",
  "NF-IDENTITY-003",
  "NF-IDENTITY-004",
  "NF-IDENTITY-005",
  "NF-IDENTITY-006",
]);
const MIN_SAFE_INTEGER = -9007199254740991;
const MAX_SAFE_INTEGER = 9007199254740991;
const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "../../..");
const fixturePath = path.join(here, "vectors", "paf_identity_v1.json");

class IdentityError extends Error {
  constructor(code) {
    super(code);
    this.code = code;
  }
}

class BinaryValue {
  constructor(data) {
    this.data = data;
  }
}

function fail(code) {
  throw new IdentityError(code);
}

function scalar(value) {
  if (typeof value !== "string") {
    fail("invalid-unicode-scalar");
  }
  for (const character of value) {
    const codePoint = character.codePointAt(0);
    if (codePoint >= 0xd800 && codePoint <= 0xdfff) {
      fail("invalid-unicode-scalar");
    }
  }
  return value.normalize("NFC");
}

function quote(value) {
  return JSON.stringify(scalar(value));
}

function compareScalars(left, right) {
  const leftPoints = Array.from(left, (character) => character.codePointAt(0));
  const rightPoints = Array.from(right, (character) => character.codePointAt(0));
  for (let index = 0; index < Math.min(leftPoints.length, rightPoints.length); index += 1) {
    if (leftPoints[index] !== rightPoints[index]) {
      return leftPoints[index] - rightPoints[index];
    }
  }
  return leftPoints.length - rightPoints.length;
}

function encode(value) {
  if (value === null) {
    return "null";
  }
  if (typeof value === "boolean") {
    return value ? "true" : "false";
  }
  if (typeof value === "number") {
    if (!Number.isInteger(value)) {
      fail("unsupported-semantic-type");
    }
    if (!Number.isSafeInteger(value) || value < MIN_SAFE_INTEGER || value > MAX_SAFE_INTEGER) {
      fail("integer-out-of-range");
    }
    return String(value);
  }
  if (typeof value === "string") {
    return quote(value);
  }
  if (value instanceof BinaryValue) {
    return `{"$paf-binary":${quote(value.data.toString("base64url"))}}`;
  }
  if (Array.isArray(value)) {
    return `[${value.map(encode).join(",")}]`;
  }
  if (typeof value === "object") {
    const entries = [];
    const seen = new Set();
    for (const [key, child] of Object.entries(value)) {
      const normalized = scalar(key);
      if (seen.has(normalized)) {
        fail("non-nfc-collision");
      }
      seen.add(normalized);
      entries.push([normalized, child]);
    }
    if (entries.length === 1 && entries[0][0] === "$paf-binary") {
      fail("reserved-binary-tag");
    }
    entries.sort(([left], [right]) => compareScalars(left, right));
    return `{${entries.map(([key, child]) => `${quote(key)}:${encode(child)}`).join(",")}}`;
  }
  fail("unsupported-semantic-type");
}

function frame(value) {
  const bytes = Buffer.isBuffer(value) ? value : Buffer.from(value, "utf8");
  const length = Buffer.alloc(8);
  length.writeBigUInt64BE(BigInt(bytes.length));
  return Buffer.concat([length, bytes]);
}

function typedDigest(domain, value) {
  const canonical = Buffer.from(encode(value), "utf8");
  const digest = createHash("sha256")
    .update(
      Buffer.concat([
        Buffer.from("PAF-DIGEST-1", "ascii"),
        frame("sha256"),
        frame(domain),
        frame(PROFILE),
        frame(canonical),
      ]),
    )
    .digest("hex");
  return `td1:${PROFILE}:${domain}:sha256:${digest}`;
}

function parseJsonText(text) {
  if (typeof text !== "string" || text.startsWith("\ufeff")) {
    fail("invalid-json-text");
  }
  let index = 0;

  function whitespace() {
    while (text[index] === " " || text[index] === "\t" || text[index] === "\r" || text[index] === "\n") {
      index += 1;
    }
  }

  function binary(value) {
    if (typeof value !== "string" || value.includes("=") || !/^[A-Za-z0-9_-]*$/.test(value)) {
      fail("invalid-binary");
    }
    const data = Buffer.from(value, "base64url");
    if (data.toString("base64url") !== value) {
      fail("invalid-binary");
    }
    return new BinaryValue(data);
  }

  function string() {
    const start = index;
    index += 1;
    let escaped = false;
    while (index < text.length) {
      const character = text[index++];
      if (escaped) {
        escaped = false;
      } else if (character === "\\") {
        escaped = true;
      } else if (character === '"') {
        try {
          return JSON.parse(text.slice(start, index));
        } catch {
          fail("invalid-json-text");
        }
      } else if (character.codePointAt(0) < 0x20) {
        fail("invalid-json-text");
      }
    }
    fail("invalid-json-text");
  }

  function value() {
    whitespace();
    const character = text[index];
    if (character === '"') {
      return string();
    }
    if (character === "{") {
      index += 1;
      whitespace();
      const object = {};
      const keys = new Set();
      if (text[index] === "}") {
        index += 1;
        return object;
      }
      while (true) {
        whitespace();
        if (text[index] !== '"') {
          fail("invalid-json-text");
        }
        const key = string();
        if (keys.has(key)) {
          fail("duplicate-object-key");
        }
        keys.add(key);
        whitespace();
        if (text[index++] !== ":") {
          fail("invalid-json-text");
        }
        object[key] = value();
        whitespace();
        if (text[index] === "}") {
          index += 1;
          if (keys.size === 1 && keys.has("$paf-binary")) {
            return binary(object["$paf-binary"]);
          }
          return object;
        }
        if (text[index++] !== ",") {
          fail("invalid-json-text");
        }
      }
    }
    if (character === "[") {
      index += 1;
      whitespace();
      const array = [];
      if (text[index] === "]") {
        index += 1;
        return array;
      }
      while (true) {
        array.push(value());
        whitespace();
        if (text[index] === "]") {
          index += 1;
          return array;
        }
        if (text[index++] !== ",") {
          fail("invalid-json-text");
        }
      }
    }
    for (const [literal, parsed] of [["true", true], ["false", false], ["null", null]]) {
      if (text.startsWith(literal, index)) {
        index += literal.length;
        return parsed;
      }
    }
    const number = /^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?/.exec(text.slice(index));
    if (number) {
      index += number[0].length;
      return Number(number[0]);
    }
    fail("invalid-json-text");
  }

  const parsed = value();
  whitespace();
  if (index !== text.length) {
    fail("invalid-json-text");
  }
  return parsed;
}

function assertEqual(vector, operation, expected, actual) {
  if (expected !== actual) {
    throw new Error(
      `${vector}: ${operation}: expected=${JSON.stringify(expected)} actual=${JSON.stringify(actual)} reason=mismatch`,
    );
  }
}

function assertRejected(vector, operation, expectedCode, action) {
  try {
    action();
  } catch (error) {
    const actualCode = error instanceof IdentityError ? error.code : error.message;
    if (actualCode === expectedCode) {
      return;
    }
    throw new Error(
      `${vector}: ${operation}: expected=${JSON.stringify(expectedCode)} actual=${JSON.stringify(actualCode)} reason=wrong-rejection`,
    );
  }
  throw new Error(
    `${vector}: ${operation}: expected=${JSON.stringify(expectedCode)} actual="accepted" reason=missing-rejection`,
  );
}

function requireExactObject(vector, value, required, operation) {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new Error(`${vector}: ${operation}: expected="object" actual=${JSON.stringify(value)} reason=malformed`);
  }
  const actual = Object.keys(value).sort().join(",");
  const expected = [...required].sort().join(",");
  assertEqual(vector, operation, expected, actual);
}

function validateManifest(data) {
  requireExactObject("manifest", data, ["vector_schema", "profile", "decisions", "canonical", "digests", "json_text", "rejections"], "fields");
  assertEqual("manifest", "schema", SCHEMA, data.vector_schema);
  assertEqual("manifest", "profile", PROFILE, data.profile);
  if (!Array.isArray(data.decisions)) {
    throw new Error("manifest: decisions: expected=\"array\" actual=\"non-array\" reason=malformed");
  }
  const decisions = new Set(data.decisions);
  assertEqual("manifest", "decisions", [...REQUIRED_DECISIONS].sort().join(","), [...decisions].sort().join(","));
  for (const collection of ["canonical", "digests", "json_text", "rejections"]) {
    if (!Array.isArray(data[collection]) || data[collection].length === 0) {
      throw new Error(`manifest: ${collection}: expected="non-empty array" actual=${JSON.stringify(data[collection])} reason=malformed`);
    }
  }
  const requiredIds = {
    canonical: REQUIRED_CANONICAL_IDS,
    digests: REQUIRED_DIGEST_IDS,
    json_text: REQUIRED_JSON_TEXT_IDS,
    rejections: REQUIRED_REJECTION_IDS,
  };
  for (const [collection, expected] of Object.entries(requiredIds)) {
    const actual = new Set(data[collection].map((vector) => vector.id));
    assertEqual(
      "manifest",
      `${collection}-ids`,
      [...expected].sort().join(","),
      [...actual].sort().join(","),
    );
  }
}

function validateCanonical(vectors) {
  for (const vector of vectors) {
    requireExactObject(vector.id ?? "canonical", vector, ["id", "value", "hex"], "fields");
    const actual = Buffer.from(encode(vector.value), "utf8").toString("hex");
    assertEqual(vector.id, "canonical-hex", vector.hex, actual);
  }
}

function validateDigests(vectors) {
  for (const vector of vectors) {
    requireExactObject(vector.id ?? "digest", vector, ["id", "domain", "value", "wire"], "fields");
    const actual = typedDigest(vector.domain, vector.value);
    assertEqual(vector.id, "typed-digest", vector.wire, actual);
    const tampered = `${vector.wire.slice(0, -1)}${vector.wire.endsWith("0") ? "1" : "0"}`;
    if (typedDigest(vector.domain, vector.value) === tampered) {
      throw new Error(`${vector.id}: tampered-digest: expected="rejected" actual="accepted" reason=tamper-undetected`);
    }
  }
}

function validateJsonText(vectors) {
  for (const vector of vectors) {
    requireExactObject(vector.id ?? "json-text", vector, ["id", "input", "hex"], "fields");
    const actual = Buffer.from(encode(parseJsonText(vector.input)), "utf8").toString("hex");
    assertEqual(vector.id, "json-text-hex", vector.hex, actual);
  }
}

function validateRejections(vectors) {
  for (const vector of vectors) {
    requireExactObject(vector.id ?? "rejection", vector, ["id", "kind", "input", "code"], "fields");
    if (vector.kind === "json-text") {
      assertRejected(vector.id, "json-text", vector.code, () => {
        encode(parseJsonText(vector.input));
      });
    } else if (vector.kind === "canonical-value") {
      assertRejected(vector.id, "canonical-value", vector.code, () => {
        encode(vector.input);
      });
    } else {
      throw new Error(`${vector.id}: rejection-kind: expected="known kind" actual=${JSON.stringify(vector.kind)} reason=unsupported`);
    }
  }
}

function validateTampering(data) {
  const firstCanonical = data.canonical[0];
  const tamperedHex = `${firstCanonical.hex.slice(0, -1)}${firstCanonical.hex.endsWith("0") ? "1" : "0"}`;
  const actual = Buffer.from(encode(firstCanonical.value), "utf8").toString("hex");
  if (actual === tamperedHex) {
    throw new Error(`${firstCanonical.id}: tampered-canonical: expected="rejected" actual="accepted" reason=tamper-undetected`);
  }
}

function runPythonReference() {
  if (process.env.PAF_IDENTITY_NODE_ONLY === "1") {
    return;
  }
  try {
    execFileSync(
      "python3",
      [path.join(here, "verify_cross_language_vectors.py")],
      {
        cwd: root,
        encoding: "utf8",
        env: { ...process.env, PAF_IDENTITY_NODE_ONLY: "1", PYTHONDONTWRITEBYTECODE: "1" },
        stdio: "pipe",
      },
    );
  } catch (error) {
    const output = error.stdout?.toString() || error.stderr?.toString() || error.message;
    throw new Error(`python-reference: expected="success" actual="failure" reason=${JSON.stringify(output.trim())}`);
  }
}

function main() {
  if (process.argv.length !== 2) {
    throw new Error(
      `arguments: expected=[] actual=${JSON.stringify(process.argv.slice(2))} reason=unexpected-argument`,
    );
  }
  const data = JSON.parse(readFileSync(fixturePath, "utf8"));
  validateManifest(data);
  validateCanonical(data.canonical);
  validateDigests(data.digests);
  validateJsonText(data.json_text);
  validateRejections(data.rejections);
  validateTampering(data);
  runPythonReference();
  console.log("paf identity vectors: ok");
}

try {
  main();
} catch (error) {
  console.error(`paf identity vectors: ${error.message}`);
  process.exitCode = 1;
}