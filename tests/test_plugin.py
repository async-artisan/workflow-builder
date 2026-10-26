import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from build_plugin import SCHEMA, build_package, validate_manifest, validate_package


class AgentPluginTests(unittest.TestCase):
    def test_manifest_matches_agent_plugins_schema(self):
        manifest = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["$schema"], SCHEMA)
        self.assertEqual(validate_manifest(manifest), [])
        self.assertNotIn("mcpServers", manifest)
        self.assertNotIn("skills", manifest)

    def test_unknown_or_incomplete_manifest_is_rejected(self):
        manifest = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
        manifest["skills"] = "./skills/"
        manifest["homepage"] = "http://example.com"
        errors = validate_manifest(manifest)
        self.assertTrue(any("未知顶层字段" in error for error in errors))
        self.assertTrue(any("HTTPS" in error for error in errors))

    def test_package_has_portable_layout_and_is_deterministic(self):
        with tempfile.TemporaryDirectory() as td:
            first = Path(td) / "first.zip"
            second = Path(td) / "second.zip"
            _manifest, count = build_package(ROOT, first)
            build_package(ROOT, second)
            self.assertGreater(count, 20)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual(validate_package(first), [])
            with zipfile.ZipFile(first) as archive:
                names = set(archive.namelist())
                self.assertIn("plugin.json", names)
                self.assertIn("skills/workflow-builder/SKILL.md", names)
                self.assertIn("skills/workflow-builder/references/capability-composition.md", names)
                self.assertNotIn("SKILL.md", names)
                self.assertNotIn("mcp.json", names)
                self.assertFalse(any("/dist/" in name or "/.git/" in name for name in names))


if __name__ == "__main__":
    unittest.main()
