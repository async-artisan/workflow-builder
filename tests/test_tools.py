import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from build_release import build_release, verify_release
from release_utils import compute_release_id, sha256_bytes
from sop_to_skill import parse_sop, render_skill
from validate_run import validate_manifest


class SopGeneratorTests(unittest.TestCase):
    def test_template_and_example_are_valid(self):
        for path in (ROOT / "assets/sop.template.md", ROOT / "examples/readonly-minutes/workflow.sop.md"):
            frontmatter, body, parameters = parse_sop(path.read_text(encoding="utf-8"))
            self.assertTrue(frontmatter["name"])
            self.assertTrue(parameters)
            self.assertIn("name:", render_skill(frontmatter, body))

    def test_invalid_parameter_is_rejected(self):
        text = (ROOT / "assets/sop.template.md").read_text(encoding="utf-8")
        text = text.replace("| task_name | string | yes |", "| Task Name | string | maybe |")
        with self.assertRaisesRegex(ValueError, "snake_case"):
            parse_sop(text)


class ReleaseTests(unittest.TestCase):
    def test_release_is_deterministic_and_detects_drift(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            (base / "a.txt").write_text("a", encoding="utf-8")
            (base / "b.txt").write_text("b", encoding="utf-8")
            release = build_release(base, [base / "b.txt", base / "a.txt"])
            again = build_release(base, [base / "a.txt", base / "b.txt"])
            self.assertEqual(release, again)
            release_path = base / "release.json"
            release_path.write_text(json.dumps(release), encoding="utf-8")
            self.assertEqual(verify_release(base, release_path), [])
            (base / "a.txt").write_text("changed", encoding="utf-8")
            self.assertTrue(verify_release(base, release_path))

    def test_release_rejects_files_outside_base(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td) / "base"
            base.mkdir()
            outside = Path(td) / "outside.txt"
            outside.write_text("x", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "base-dir"):
                build_release(base, [outside])


def valid_manifest():
    files = [
        {"path": "workflow.sop.md", "sha256": sha256_bytes(b"sop")},
        {"path": "SKILL.md", "sha256": sha256_bytes(b"skill")},
    ]
    release_id = compute_release_id(files)
    return {
        "run_id": "run-test",
        "run_state": "in_progress",
        "workflow": {"name": "example", "version": "1.0.0"},
        "release": {"release_id": release_id, "files": files},
        "mode": "trial",
        "risk_tier": "read_only",
        "input": {"digest": sha256_bytes(b"input"), "source": "fixture", "synthetic": True},
        "steps": [
            {
                "step_id": "extract",
                "state": "completed",
                "attempt": 1,
                "input_digest": sha256_bytes(b"input"),
                "output_digest": sha256_bytes(b"output"),
                "evidence": ["artifacts/output.md"],
                "side_effect": "none",
                "external_state": "not_attempted",
                "side_effect_intent": None,
                "idempotency_key": None,
                "recovery": None,
                "external_receipt": None,
            }
        ],
        "checks": [{"check_id": "A-01", "critical": True, "state": "passed", "evidence": "assertions/A-01"}],
        "approvals": [],
        "evaluation": {"case_id": None, "baseline_id": None, "distinct_from_tuning": False, "threshold_met": False},
        "handoff": {"independent_session": False, "entry_verified": False, "continue_verified": False, "evidence": None},
        "dry_run_evidence": None,
        "budget": {
            "max_attempts": 2,
            "max_tool_calls": 5,
            "max_minutes": 10,
            "max_cost": 1,
            "actual_tool_calls": 1,
            "actual_minutes": 2,
            "actual_cost": 0.1,
            "on_exhaust": "stop",
        },
        "declared_status": {
            "designed": True,
            "tested": True,
            "human_approved": False,
            "reuse_validated": False,
            "handoff_validated": False,
        },
    }


class RunValidationTests(unittest.TestCase):
    def test_valid_read_only_manifest(self):
        derived, errors = validate_manifest(valid_manifest())
        self.assertEqual(errors, [])
        self.assertTrue(derived["tested"])
        self.assertFalse(derived["reuse_validated"])

    def test_reuse_overclaim_is_rejected(self):
        data = valid_manifest()
        data["declared_status"]["reuse_validated"] = True
        _derived, errors = validate_manifest(data)
        self.assertTrue(any("reuse_validated" in error for error in errors))

    def test_reuse_can_be_derived_from_complete_evaluation(self):
        data = valid_manifest()
        data["evaluation"] = {
            "case_id": "case-unseen-1",
            "baseline_id": "baseline-1",
            "distinct_from_tuning": True,
            "threshold_met": True,
        }
        data["declared_status"]["reuse_validated"] = True
        derived, errors = validate_manifest(data)
        self.assertEqual(errors, [])
        self.assertTrue(derived["reuse_validated"])

    def test_release_tampering_is_rejected(self):
        data = valid_manifest()
        data["release"]["release_id"] = "sha256:" + "0" * 64
        derived, errors = validate_manifest(data)
        self.assertFalse(derived["designed"])
        self.assertTrue(any("release_id" in error for error in errors))

    def test_restricted_write_requires_current_release_approval(self):
        data = valid_manifest()
        data["risk_tier"] = "restricted_write"
        data["dry_run_evidence"] = "dry-run/1"
        step = data["steps"][0]
        step.update({
            "side_effect": "restricted_write",
            "external_state": "succeeded",
            "side_effect_intent": "create test object",
            "idempotency_key": "run-test-extract-1",
            "external_receipt": "receipt-1",
        })
        _derived, errors = validate_manifest(data)
        self.assertTrue(any("人工批准" in error for error in errors))

        data["approvals"] = [{
            "approver": "Business Owner",
            "decision": "approved",
            "quote": "批准本次受控试跑",
            "release_id": data["release"]["release_id"],
            "scope": "test object only",
            "evidence": "approval/1",
        }]
        data["declared_status"]["human_approved"] = True
        derived, errors = validate_manifest(data)
        self.assertEqual(errors, [])
        self.assertTrue(derived["human_approved"])

    def test_unknown_external_result_cannot_be_retried(self):
        data = valid_manifest()
        data["risk_tier"] = "reversible_write"
        step = data["steps"][0]
        step.update({
            "state": "running",
            "attempt": 2,
            "side_effect": "reversible_write",
            "external_state": "unknown",
            "side_effect_intent": "update test object",
            "idempotency_key": "run-test-extract",
        })
        data["declared_status"]["tested"] = False
        _derived, errors = validate_manifest(data)
        self.assertTrue(any("禁止直接完成或重试" in error for error in errors))

    def test_budget_overrun_requires_exhausted_state(self):
        data = valid_manifest()
        data["budget"]["actual_tool_calls"] = 6
        _derived, errors = validate_manifest(data)
        self.assertTrue(any("budget_exhausted" in error for error in errors))
        data["run_state"] = "budget_exhausted"
        _derived, errors = validate_manifest(data)
        self.assertEqual(errors, [])

    def test_completed_run_requires_critical_checks(self):
        data = valid_manifest()
        data["run_state"] = "completed"
        data["checks"][0]["state"] = "not_run"
        data["checks"][0]["evidence"] = None
        _derived, errors = validate_manifest(data)
        self.assertTrue(any("关键检查" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
