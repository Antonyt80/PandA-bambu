#!/usr/bin/env python3
"""Offline smoke tests for the revision-3 PAF bootstrap bundle."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


class BundleSmoke(unittest.TestCase):
    root: Path

    @classmethod
    def setUpClass(cls) -> None:
        cls.root = ROOT

    def test_required_files(self) -> None:
        required = [
            "documentation/evolvehls/paf-product-roadmap.md",
            "documentation/evolvehls/paf-runtime-specification.md",
            "documentation/evolvehls/paf-security-data-governance-plan.md",
            "documentation/evolvehls/paf-observability-operations-plan.md",
            "documentation/evolvehls/paf-bootstrap-operational-invariants.md",
            "documentation/evolvehls/paf-bootstrap-self-hosting-plan.md",
            "documentation/evolvehls/paf-responsibility-transfer-matrix.md",
            "documentation/evolvehls/paf-interface-state-machine-map.md",
            "documentation/evolvehls/paf-revision-3-critical-review.md",
            "config/paf-bootstrap-campaign.json",
            "config/schemas/paf-bootstrap-campaign.schema.json",
            "config/schemas/paf-bootstrap-task.schema.json",
            "tools/paf-bootstrap/templates/next-task-prompt.md",
            "tools/paf-bootstrap/paf-cline-cycle",
            "tools/paf-bootstrap/paf-cline-next-task",
            "tools/paf-bootstrap/paf-cline-campaign",
            "tools/paf-bootstrap/paf-cline-monitor",
            "tools/paf-bootstrap/paf-cline-preflight",
            "tools/paf-bootstrap/paf-cline-review-resume",
            "tools/paf-bootstrap/paf-validation-runner",
            "tools/paf-bootstrap/validation_policy.py",
        ]
        missing = [path for path in required if not (self.root / path).is_file()]
        self.assertEqual([], missing)

    def test_config_and_backlog(self) -> None:
        config = json.loads((self.root / "config/paf-bootstrap-campaign.json").read_text())
        self.assertEqual(2, config["schema_version"])
        self.assertEqual(3, config["version"])
        ids = [item["id"] for item in config["backlog"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual("BS-000", ids[0])
        self.assertIn("BS-025", ids)
        self.assertIn("BS-035", ids)
        known = set(ids)
        for item in config["backlog"]:
            self.assertTrue(set(item["depends_on"]).issubset(known))
        bundled_docs = {
            path for path in config["documents"].values()
            if Path(path).name in {
                "paf-product-roadmap.md", "paf-runtime-specification.md",
                "paf-security-data-governance-plan.md", "paf-observability-operations-plan.md",
                "paf-bootstrap-operational-invariants.md", "paf-bootstrap-self-hosting-plan.md",
                "paf-responsibility-transfer-matrix.md", "paf-interface-state-machine-map.md",
                "paf-revision-3-critical-review.md",
            }
        }
        for path in bundled_docs:
            self.assertTrue((self.root / path).is_file(), path)

    def test_script_syntax(self) -> None:
        cycle = self.root / "tools/paf-bootstrap/paf-cline-cycle"
        result = subprocess.run(["bash", "-n", str(cycle)], check=False)
        self.assertEqual(0, result.returncode)
        for name in (
            "paf-cline-next-task", "paf-cline-campaign", "paf-cline-monitor",
            "paf-cline-preflight", "paf-cline-review-resume", "paf-validation-runner",
            "validation_policy.py",
        ):
            result = subprocess.run(["python3", "-m", "py_compile", str(self.root / "tools/paf-bootstrap" / name)], check=False)
            self.assertEqual(0, result.returncode, name)

    def test_node_validation_authorization(self) -> None:
        import sys

        sys.path.insert(0, str(self.root / "tools/paf-bootstrap"))
        try:
            from validation_policy import ValidationAuthorizationError, authorize_validation_command

            for command, suffix in (
                ("node tests/paf/identity/verify_vectors.mjs", ".mjs"),
                ("node tests/paf/identity/example.js", ".js"),
                ("node scripts/paf/example.cjs", ".cjs"),
            ):
                authorized = authorize_validation_command(command)
                self.assertEqual("node", authorized.executable)
                self.assertEqual("node-approved-repository-script-v1", authorized.authorization_rule)
                self.assertTrue(authorized.normalized_paths[0].endswith(suffix))
            for command in (
                "node ../verify_vectors.mjs",
                "node /tmp/verify_vectors.mjs",
                "node tests/paf/identity/verify_vectors.mjs && echo unsafe",
                "node tests/paf/identity/verify_vectors.mjs; echo unsafe",
                'node -e "process.exit(0)"',
                "node arbitrary-script.mjs",
                "node tests/paf/identity/verify_vectors.mjs unexpected-argument",
            ):
                with self.assertRaises(ValidationAuthorizationError, msg=command):
                    authorize_validation_command(command)
        finally:
            sys.path.pop(0)

    def test_node_scripts_via_validation_runner(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            (repo / "tests/paf/identity").mkdir(parents=True)
            (repo / "scripts/paf").mkdir(parents=True)
            for relative in (
                "tests/paf/identity/verify_vectors.mjs",
                "tests/paf/identity/verify_vectors.js",
                "scripts/paf/verify_vectors.cjs",
            ):
                (repo / relative).write_text("process.exit(0);\n", encoding="utf-8")
            manifest = Path(tmp) / "validation.json"
            audit = Path(tmp) / "audit.json"
            manifest.write_text(
                json.dumps({
                    "schema_version": 1,
                    "commands": [
                        "node tests/paf/identity/verify_vectors.mjs",
                        "node tests/paf/identity/verify_vectors.js",
                        "node scripts/paf/verify_vectors.cjs",
                    ],
                }),
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    "python3", str(self.root / "tools/paf-bootstrap/paf-validation-runner"),
                    "--repo", str(repo), "--manifest", str(manifest), "--audit", str(audit),
                ],
                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
            )
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            records = json.loads(audit.read_text(encoding="utf-8"))["commands"]
            self.assertEqual(3, len(records))
            self.assertEqual(
                [
                    "tests/paf/identity/verify_vectors.mjs",
                    "tests/paf/identity/verify_vectors.js",
                    "scripts/paf/verify_vectors.cjs",
                ],
                [record["normalized_paths"][0] for record in records],
            )
            for record in records:
                self.assertEqual("node", record["executable"])
                self.assertEqual("node-approved-repository-script-v1", record["authorization_rule"])
                self.assertEqual(0, record["exit_status"])

    def test_identity_vectors_via_validation_runner(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            shutil.copytree(self.root / "tests", repo / "tests")
            shutil.copytree(self.root / "paf", repo / "paf")
            manifest = Path(tmp) / "validation.json"
            audit = Path(tmp) / "audit.json"
            manifest.write_text(
                json.dumps({
                    "schema_version": 1,
                    "commands": ["node tests/paf/identity/verify_vectors.mjs"],
                }),
                encoding="utf-8",
            )
            runner = [
                "python3", str(self.root / "tools/paf-bootstrap/paf-validation-runner"),
                "--repo", str(repo), "--manifest", str(manifest), "--audit", str(audit),
            ]
            result = subprocess.run(
                runner, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
            )
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            record = json.loads(audit.read_text(encoding="utf-8"))["commands"][0]
            self.assertEqual("node", record["executable"])
            self.assertEqual(["tests/paf/identity/verify_vectors.mjs"], record["arguments"])
            self.assertEqual("node-approved-repository-script-v1", record["authorization_rule"])
            self.assertEqual(["tests/paf/identity/verify_vectors.mjs"], record["normalized_paths"])
            self.assertEqual(0, record["exit_status"])

            fixture = repo / "tests/paf/identity/vectors/paf_identity_v1.json"
            data = json.loads(fixture.read_text(encoding="utf-8"))
            data["digests"][0]["wire"] = data["digests"][0]["wire"][:-1] + "0"
            fixture.write_text(json.dumps(data), encoding="utf-8")
            result = subprocess.run(
                runner, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
            )
            self.assertNotEqual(0, result.returncode)
            record = json.loads(audit.read_text(encoding="utf-8"))["commands"][0]
            self.assertEqual("node", record["executable"])
            self.assertNotEqual(0, record["exit_status"])

    def test_next_task_list_eligible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "state.json"
            state.write_text(json.dumps({"schema_version": 2, "campaign_id": "paf-bootstrap-self-hosting", "completed_backlog_items": ["BS-000"], "tasks": {}, "current_task_id": None}))
            cmd = [
                str(self.root / "tools/paf-bootstrap/paf-cline-next-task"),
                "--repo", str(self.root),
                "--campaign-config", str(self.root / "config/paf-bootstrap-campaign.json"),
                "--campaign-state", str(state),
                "--output-dir", str(Path(tmp) / "tasks"),
                "--list-eligible",
            ]
            result = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual("BS-010", json.loads(result.stdout)["id"])

    def test_monitor_synthetic_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); run = root / "run"; run.mkdir(); (root / "latest").symlink_to(run)
            (run / "controller.log").write_text("[x] Starting sonnet-1 in act mode (attempt 1/1)\n")
            event = {"ts": "x", "type": "agent_event", "event": {"type": "iteration_start", "iteration": 3}}
            (run / "cycle-1-sonnet.attempt-1.jsonl").write_text(json.dumps(event) + "\n")
            result = subprocess.run([str(self.root / "tools/paf-bootstrap/paf-cline-monitor"), "--state-root", str(root), "status"], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn("sonnet-1", result.stdout)
            self.assertIn("Iteration: 3", result.stdout)

    def test_campaign_init(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"; repo.mkdir()
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            config_dir = repo / "config"; config_dir.mkdir()
            (config_dir / "paf-bootstrap-campaign.json").write_text((self.root / "config/paf-bootstrap-campaign.json").read_text())
            state = Path(tmp) / "campaign"
            command = [str(self.root / "tools/paf-bootstrap/paf-cline-campaign"), "--repo", str(repo), "--state", str(state), "init", "--complete", "BS-000"]
            result = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
            self.assertEqual(0, result.returncode, result.stderr)
            saved = json.loads((state / "campaign-state.json").read_text())
            self.assertEqual(["BS-000"], saved["completed_backlog_items"])


    def test_review_resume_preserves_sonnet_provider_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            fake_bin = root / "bin"
            home = root / "home"
            state = root / "state"
            fake_bin.mkdir()
            (home / ".cline-opus").mkdir(parents=True)
            (home / ".cline-sonnet").mkdir(parents=True)
            state.mkdir()
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.name", "PAF Smoke"], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.email", "paf-smoke@example.invalid"], check=True)
            (repo / "README.md").write_text("base\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(repo), "add", "README.md"], check=True)
            subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "base"], check=True)
            head = subprocess.run(
                ["git", "-C", str(repo), "rev-parse", "HEAD"],
                text=True, stdout=subprocess.PIPE, check=True,
            ).stdout.strip()
            (state / "task.md").write_text("# Review task\n", encoding="utf-8")
            (state / "base-sha.txt").write_text(head + "\n", encoding="utf-8")
            (state / "cycle-1-head-sha.txt").write_text(head + "\n", encoding="utf-8")
            (state / "cycle-1-terra.txt").write_text("Implementation complete\n", encoding="utf-8")
            (state / "review-resume-20260805T003621Z-opus.txt").write_text(
                "Plan\nREVIEW_PLAN_STATUS=READY\n", encoding="utf-8"
            )

            fake_cline = fake_bin / "cline"
            fake_cline.write_text(
                """#!/usr/bin/env python3
import json
import pathlib
import sys

config = sys.argv[sys.argv.index("--config") + 1]
pathlib.Path(__import__("os").environ["CLINE_CALL_LOG"]).write_text(pathlib.Path(config).name + "\\n", encoding="utf-8")
print(json.dumps({"type": "agent_event", "event": {"type": "error", "error": {"message": "BedrockException: tools.0.custom.strict: Extra inputs are not permitted"}}}))
print(json.dumps({"type": "run_result", "finishReason": "error", "text": "BedrockException: tools.0.custom.strict: Extra inputs are not permitted"}))
raise SystemExit(1)
""",
                encoding="utf-8",
            )
            fake_cline.chmod(0o755)
            call_log = root / "cline-calls.log"
            env = os.environ.copy()
            env.update({
                "PATH": f"{fake_bin}:{env.get('PATH', '')}",
                "HOME": str(home),
                "LITELLM_API_KEY": "smoke-key",
                "OPENAI_API_KEY": "smoke-key",
                "CLINE_CALL_LOG": str(call_log),
            })
            result = subprocess.run(
                [
                    str(self.root / "tools/paf-bootstrap/paf-cline-review-resume"),
                    "--state-dir", str(state), "--repo", str(repo), "--from", "sonnet",
                ],
                env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
            )
            self.assertEqual(1, result.returncode, result.stdout + result.stderr)
            self.assertIn("Review resume failed at Sonnet", result.stderr)
            self.assertIn("tools.0.custom.strict", result.stderr)
            self.assertIn("Summary:", result.stderr)
            summaries = list(state.glob("review-resume-*-summary.json"))
            self.assertEqual(1, len(summaries))
            summary = json.loads(summaries[0].read_text(encoding="utf-8"))
            self.assertEqual("failed", summary["status"])
            self.assertEqual("sonnet", summary["role"])
            self.assertIn("tools.0.custom.strict", summary["reason"])
            self.assertEqual(".cline-sonnet\n", call_log.read_text(encoding="utf-8"))

    def test_controller_mock_end_to_end(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            origin = root / "origin.git"
            repo = root / "repo"
            fake_bin = root / "bin"
            home = root / "home"
            fake_bin.mkdir()
            home.mkdir()
            for profile in (".cline-sol", ".cline-terra", ".cline-opus", ".cline-sonnet"):
                (home / profile).mkdir()

            subprocess.run(["git", "init", "--bare", "-q", str(origin)], check=True)
            subprocess.run(["git", "clone", "-q", str(origin), str(repo)], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.name", "PAF Smoke"], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.email", "paf-smoke@example.invalid"], check=True)
            (repo / "README.md").write_text("base\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(repo), "add", "README.md"], check=True)
            subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "base"], check=True)
            subprocess.run(["git", "-C", str(repo), "branch", "-M", "dev/panda"], check=True)
            subprocess.run(["git", "-C", str(repo), "push", "-q", "-u", "origin", "dev/panda"], check=True)

            fake_cline = fake_bin / "cline"
            fake_cline.write_text(
                """#!/usr/bin/env python3
import json
import pathlib
import sys

args = sys.argv[1:]
config = ""
cwd = "."
for index, value in enumerate(args):
    if value == "--config":
        config = args[index + 1]
    elif value == "--cwd":
        cwd = args[index + 1]

role = pathlib.Path(config).name
if role == ".cline-sol":
    final = "Mock plan\\nPLAN_STATUS=READY"
elif role == ".cline-terra":
    (pathlib.Path(cwd) / "implemented.txt").write_text("implemented\\n", encoding="utf-8")
    final = "Mock implementation\\nIMPLEMENTATION_STATUS=COMPLETE"
elif role == ".cline-opus":
    final = "Mock review plan\\nREVIEW_PLAN_STATUS=READY"
elif role == ".cline-sonnet":
    final = "Mock approval\\nPAF_REVIEW_VERDICT=APPROVED"
else:
    raise SystemExit("unknown profile")

print(json.dumps({"type": "agent_event", "event": {"type": "iteration_start", "iteration": 1}}), flush=True)
print(json.dumps({"type": "run_result", "finishReason": "completed", "text": final}), flush=True)
""",
                encoding="utf-8",
            )
            fake_cline.chmod(0o755)

            task = root / "task.md"
            task.write_text("# Mock task\n\nCreate implemented.txt.\n", encoding="utf-8")
            state_root = root / "runs"

            env = os.environ.copy()
            env.update(
                {
                    "PATH": f"{fake_bin}:{env.get('PATH', '')}",
                    "HOME": str(home),
                    "LITELLM_API_KEY": "smoke-key",
                    "OPENAI_API_KEY": "smoke-key",
                    "PAF_REPO": str(repo),
                    "PAF_BRANCH": "agent/mock-controller",
                    "PAF_BASE_BRANCH": "dev/panda",
                    "PAF_PUBLISH": "0",
                    "PAF_STAGE_MAX_ATTEMPTS": "1",
                    "PAF_REVIEW_STAGE_MAX_ATTEMPTS": "1",
                    "PAF_PRECOMMIT_VALIDATION_MANIFEST": str(root / "validation.json"),
                    "PAF_VALIDATION_RUNNER": str(self.root / "tools/paf-bootstrap/paf-validation-runner"),
                    "PAF_STATE_ROOT": str(state_root),
                    "PAF_GLOBAL_LOG": str(root / "global.log"),
                }
            )
            (root / "validation.json").write_text(
                json.dumps({"schema_version": 1, "commands": ["git diff --check"]}),
                encoding="utf-8",
            )
            result = subprocess.run(
                [str(self.root / "tools/paf-bootstrap/paf-cline-cycle"), str(task)],
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                timeout=45,
            )
            self.assertEqual(0, result.returncode, result.stdout + "\n" + result.stderr)
            latest = (state_root / "latest").resolve()
            summary = json.loads((latest / "run-summary.json").read_text(encoding="utf-8"))
            self.assertEqual("approved", summary["status"])
            self.assertEqual("sonnet-1", summary["role"])
            audit = json.loads((latest / "cycle-1-controller-validation.audit.json").read_text(encoding="utf-8"))
            self.assertEqual("git", audit["commands"][0]["executable"])
            self.assertEqual(0, audit["commands"][0]["exit_status"])
            self.assertEqual("implemented\n", (repo / "implemented.txt").read_text(encoding="utf-8"))
            status = subprocess.run(
                ["git", "-C", str(repo), "status", "--porcelain"],
                text=True,
                stdout=subprocess.PIPE,
                check=True,
            ).stdout
            self.assertEqual("", status)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--bundle-root", required=True)
    args, remaining = parser.parse_known_args()
    ROOT = Path(args.bundle_root).resolve()
    unittest.main(argv=[__file__, *remaining])
