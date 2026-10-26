import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class DiscoveryResourceTests(unittest.TestCase):
    def test_discovery_cases_have_behavior_and_failure_oracles(self):
        cases = []
        for path in sorted((ROOT / "evals/cases").glob("discovery-*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertTrue(data["case_id"])
            self.assertTrue(data["initial_prompt"])
            self.assertGreaterEqual(len(data["expected_behavior"]), 3)
            self.assertTrue(data["critical_failures"])
            self.assertTrue(data["measurements"])
            self.assertTrue(data["synthetic"])
            cases.append(data["case_id"])
        self.assertEqual(len(cases), len(set(cases)))
        self.assertIn("discovery-vague-v1", cases)
        self.assertIn("discovery-clear-v1", cases)
        self.assertIn("discovery-fragmented-v1", cases)

    def test_interview_is_linked_and_preserves_confirmed_vs_suggested(self):
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        interview = (ROOT / "references/discovery-interview.md").read_text(encoding="utf-8")
        brief = (ROOT / "assets/discovery-brief.template.md").read_text(encoding="utf-8")
        self.assertIn("references/discovery-interview.md", skill)
        self.assertIn("assets/workflow-card.template.md", skill)
        self.assertIn("已确认", brief)
        self.assertIn("建议默认", brief)
        self.assertIn("仍未知", brief)
        self.assertIn("业务确认之后", interview)

    def test_examples_explicitly_mark_synthetic_evidence(self):
        example = (ROOT / "examples/discovery/vague-to-mvp.md").read_text(encoding="utf-8")
        output = (ROOT / "examples/discovery/output-sample.md").read_text(encoding="utf-8")
        self.assertIn("合成对话", example)
        self.assertIn("不是由真实客户材料生成", output)


if __name__ == "__main__":
    unittest.main()
