import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CapabilityCompositionTests(unittest.TestCase):
    def test_capability_cases_cover_reuse_fallback_creation_and_write(self):
        expected = {
            "capability-existing-tools-v1",
            "capability-manual-fallback-v1",
            "capability-new-skill-v1",
            "capability-restricted-write-v1",
        }
        actual = set()
        for path in (ROOT / "evals/cases").glob("capability-*.json"):
            data = json.loads(path.read_text(encoding="utf-8"))
            actual.add(data["case_id"])
            self.assertTrue(data["initial_prompt"])
            self.assertGreaterEqual(len(data["expected_behavior"]), 3)
            self.assertTrue(data["critical_failures"])
            self.assertTrue(data["measurements"])
        self.assertEqual(actual, expected)

    def test_capability_contract_and_creation_gates_exist(self):
        reference = (ROOT / "references/capability-composition.md").read_text(encoding="utf-8")
        card = (ROOT / "assets/capability-card.template.md").read_text(encoding="utf-8")
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("references/capability-composition.md", skill)
        self.assertIn("复用与组合已有 Skill", reference)
        self.assertIn("创建新 Skill 或 MCP 的门槛", reference)
        self.assertIn("宿主实际调用方式", card)
        self.assertIn("不可用时的跳过", card)

    def test_software_testing_example_marks_candidates_unverified(self):
        example = (ROOT / "examples/software-testing/capability-plan.md").read_text(encoding="utf-8")
        self.assertIn("合成设计示例", example)
        self.assertIn("不代表任何宿主已经安装", example)
        self.assertIn("不默认创建任何新组件", example)


if __name__ == "__main__":
    unittest.main()
