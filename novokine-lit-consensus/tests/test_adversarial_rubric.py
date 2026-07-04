#!/usr/bin/env python3
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUBRIC = ROOT / "references" / "adversarial_rubric.json"
SCRIPT = ROOT / "scripts" / "claude_adversarial_rubric.mjs"


class AdversarialRubricTest(unittest.TestCase):
    def test_checked_in_rubric_has_ten_adversarial_design_agents(self):
        data = json.loads(RUBRIC.read_text())
        self.assertEqual(data["design_process"]["agent_count"], 10)
        self.assertIn("design", data["design_process"]["method"].lower())
        self.assertEqual(len(data["rubric_design_agents"]), 10)
        self.assertEqual(len({a["id"] for a in data["rubric_design_agents"]}), 10)
        for agent in data["rubric_design_agents"]:
            for field in (
                "id",
                "name",
                "design_principle",
                "required_fields",
                "decision_rules",
                "failure_tests",
                "acceptance_standard",
                "rubric_contribution",
            ):
                self.assertIn(field, agent)
            self.assertGreaterEqual(len(agent["required_fields"]), 3)
            self.assertGreaterEqual(len(agent["decision_rules"]), 3)
            self.assertGreaterEqual(len(agent["failure_tests"]), 3)

    def test_checked_in_rubric_has_ten_adversarial_agents(self):
        data = json.loads(RUBRIC.read_text())
        self.assertEqual(data["schema_version"], "novokine-adversarial-rubric-v1")
        self.assertEqual(data["rubric_owner"], "claude-agent-sdk")
        self.assertEqual(len(data["adversarial_agents"]), 10)
        self.assertEqual(len({a["id"] for a in data["adversarial_agents"]}), 10)
        for agent in data["adversarial_agents"]:
            for field in (
                "id",
                "name",
                "adversarial_question",
                "failure_modes",
                "required_checks",
                "red_flags",
                "pass_standard",
                "output_fields",
            ):
                self.assertIn(field, agent)
            self.assertGreaterEqual(len(agent["failure_modes"]), 3)
            self.assertGreaterEqual(len(agent["required_checks"]), 3)

    def test_rubric_covers_direction_likelihood_and_provenance(self):
        data = json.loads(RUBRIC.read_text())
        lanes = {lane["id"] for lane in data["decision_lanes"]}
        self.assertIn("activation_direction", lanes)
        self.assertIn("novokine_likelihood", lanes)
        self.assertIn("evidence_provenance", lanes)
        self.assertIn("do_not_use", data)
        self.assertIn("differential expression as activation direction", data["do_not_use"])
        self.assertIn("Open Targets as activation direction", data["do_not_use"])

    def test_claude_sdk_wrapper_validates_rubric_and_rejects_malformed_input(self):
        subprocess.run(["node", str(SCRIPT), "--dry-run"], cwd=ROOT, check=True)
        malformed = json.loads(RUBRIC.read_text())
        malformed["adversarial_agents"] = malformed["adversarial_agents"][:9]
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            json.dump(malformed, fh)
            bad_path = fh.name
        try:
            result = subprocess.run(
                ["node", str(SCRIPT), "--dry-run", "--input", bad_path],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("exactly 10", result.stderr)
        finally:
            Path(bad_path).unlink(missing_ok=True)

    def test_claude_sdk_wrapper_rejects_missing_design_panel(self):
        malformed = json.loads(RUBRIC.read_text())
        malformed["rubric_design_agents"] = malformed["rubric_design_agents"][:9]
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            json.dump(malformed, fh)
            bad_path = fh.name
        try:
            result = subprocess.run(
                ["node", str(SCRIPT), "--dry-run", "--input", bad_path],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("rubric_design_agents must contain exactly 10", result.stderr)
        finally:
            Path(bad_path).unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
