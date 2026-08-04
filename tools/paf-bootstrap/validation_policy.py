"""Structured authorization and execution for controller-owned validation."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path, PurePosixPath
import shlex
import subprocess
from typing import Callable


FORBIDDEN_SHELL_TOKENS = (";", "&&", "||", "`", "$(", "&", "|", ">", "<", "\n", "\r", "\x00")
APPROVED_NODE_ROOTS = ("tests/paf", "scripts/paf")
APPROVED_SHELL_ROOTS = ("tools", "scripts")


class ValidationAuthorizationError(ValueError):
    """Raised when a validation command does not meet the controller policy."""


@dataclass(frozen=True)
class AuthorizedCommand:
    executable: str
    arguments: tuple[str, ...]
    authorization_rule: str
    normalized_paths: tuple[str, ...]

    @property
    def argv(self) -> list[str]:
        return [self.executable, *self.arguments]

    def audit_record(self, exit_status: int | None = None) -> dict[str, object]:
        record: dict[str, object] = {
            "executable": self.executable,
            "arguments": list(self.arguments),
            "authorization_rule": self.authorization_rule,
            "normalized_paths": list(self.normalized_paths),
        }
        if exit_status is not None:
            record["exit_status"] = exit_status
        return record


def _parse(command: str) -> list[str]:
    if not isinstance(command, str) or not command.strip():
        raise ValidationAuthorizationError("validation command must be non-empty")
    if any(token in command for token in FORBIDDEN_SHELL_TOKENS):
        raise ValidationAuthorizationError(f"unsafe validation command syntax: {command!r}")
    try:
        argv = shlex.split(command, posix=True)
    except ValueError as exc:
        raise ValidationAuthorizationError(f"invalid validation command syntax: {command!r}") from exc
    if not argv:
        raise ValidationAuthorizationError("validation command must be non-empty")
    return argv


def _normalize_relative_path(value: str, roots: tuple[str, ...], extensions: tuple[str, ...] | None = None) -> str:
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValidationAuthorizationError(f"unsafe repository-local path: {value!r}")
    normalized = path.as_posix().removeprefix("./")
    if normalized in {"", "."} or not any(normalized == root or normalized.startswith(root + "/") for root in roots):
        raise ValidationAuthorizationError(f"path is outside approved roots: {value!r}")
    if extensions is not None and path.suffix.lower() not in extensions:
        raise ValidationAuthorizationError(f"path has an unsupported extension: {value!r}")
    return normalized


def _node(argv: list[str]) -> AuthorizedCommand:
    if len(argv) != 2:
        raise ValidationAuthorizationError("node validation requires exactly one repository-local script argument")
    script = _normalize_relative_path(argv[1], APPROVED_NODE_ROOTS, (".js", ".mjs", ".cjs"))
    return AuthorizedCommand("node", (script,), "node-approved-repository-script-v1", (script,))


def _git(argv: list[str]) -> AuthorizedCommand:
    if argv != ["git", "diff", "--check"]:
        raise ValidationAuthorizationError("only 'git diff --check' is approved")
    return AuthorizedCommand("git", ("diff", "--check"), "git-diff-check-v1", ())


def _no_path_args(rule: str) -> Callable[[list[str]], AuthorizedCommand]:
    def authorize(argv: list[str]) -> AuthorizedCommand:
        return AuthorizedCommand(argv[0], tuple(argv[1:]), rule, ())
    return authorize


def _shell_script(argv: list[str]) -> AuthorizedCommand:
    if len(argv) < 2:
        raise ValidationAuthorizationError("bash validation requires a repository-local script")
    script = _normalize_relative_path(argv[1], APPROVED_SHELL_ROOTS)
    return AuthorizedCommand("bash", (script, *argv[2:]), "bash-approved-repository-script-v1", (script,))


def _direct_shell_script(argv: list[str]) -> AuthorizedCommand:
    script = _normalize_relative_path(argv[0], APPROVED_SHELL_ROOTS)
    return AuthorizedCommand(script, tuple(argv[1:]), "direct-approved-repository-script-v1", (script,))


EXECUTOR_REGISTRY: dict[str, Callable[[list[str]], AuthorizedCommand]] = {
    "node": _node,
    "git": _git,
    "python": _no_path_args("python-validation-v1"),
    "python3": _no_path_args("python3-validation-v1"),
    "pytest": _no_path_args("pytest-validation-v1"),
    "ctest": _no_path_args("ctest-validation-v1"),
    "ninja": _no_path_args("ninja-validation-v1"),
    "make": _no_path_args("make-validation-v1"),
    "cmake": _no_path_args("cmake-validation-v1"),
    "bash": _shell_script,
}


def authorize_validation_command(command: str) -> AuthorizedCommand:
    """Parse a validation command without a shell and authorize its argv schema."""
    argv = _parse(command)
    authorizer = EXECUTOR_REGISTRY.get(argv[0])
    if authorizer is not None:
        return authorizer(argv)
    if argv[0].startswith(("./tools/", "tools/", "./scripts/", "scripts/")):
        return _direct_shell_script(argv)
    raise ValidationAuthorizationError(f"unsupported validation executable: {argv[0]!r}")


def _validate_runtime_paths(command: AuthorizedCommand, repo: Path) -> None:
    root = repo.resolve()
    for normalized in command.normalized_paths:
        resolved = (root / normalized).resolve(strict=True)
        try:
            resolved.relative_to(root)
        except ValueError as exc:
            raise ValidationAuthorizationError(f"authorized path escapes repository: {normalized!r}") from exc
        if not resolved.is_file():
            raise ValidationAuthorizationError(f"authorized path is not a file: {normalized!r}")


def execute_authorized_command(command: AuthorizedCommand, repo: Path) -> subprocess.CompletedProcess[str]:
    """Execute a previously authorized argv without invoking a shell."""
    _validate_runtime_paths(command, repo)
    return subprocess.run(command.argv, cwd=repo, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)


def load_manifest(path: Path) -> list[str]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or not isinstance(value.get("commands"), list) or not all(isinstance(v, str) for v in value["commands"]):
        raise ValidationAuthorizationError(f"invalid validation manifest: {path}")
    return value["commands"]


def write_manifest(path: Path, commands: list[str]) -> None:
    authorized = [authorize_validation_command(command) for command in commands]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "schema_version": 1,
        "commands": commands,
        "authorized_commands": [command.audit_record() for command in authorized],
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_audit(path: Path, records: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"schema_version": 1, "commands": records}, indent=2, sort_keys=True) + "\n", encoding="utf-8")