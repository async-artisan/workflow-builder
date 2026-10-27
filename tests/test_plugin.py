import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from build_plugin import (
    RUNTIME_FILES,
    SCHEMA,
    build_package,
    build_skill_package,
    validate_manifest,
    validate_package,
)


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

    def test_plugin_package_has_allowlisted_layout_and_is_deterministic(self):
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
                expected = {"plugin.json"} | {
                    (Path("skills/workflow-builder") / relative).as_posix()
                    for relative in RUNTIME_FILES
                }
                self.assertEqual(names, expected)
                for excluded in ("tests", "evals", "examples", "docs", ".github"):
                    self.assertFalse(any(excluded in name.split("/") for name in names))

    def test_direct_skill_package_has_allowlisted_layout(self):
        with tempfile.TemporaryDirectory() as td:
            package = Path(td) / "skill.zip"
            _manifest, count = build_skill_package(ROOT, package)
            self.assertEqual(count, len(RUNTIME_FILES))
            self.assertEqual(validate_package(package), [])
            with zipfile.ZipFile(package) as archive:
                names = set(archive.namelist())
            expected = {
                (Path("workflow-builder") / relative).as_posix()
                for relative in RUNTIME_FILES
            }
            self.assertEqual(names, expected)

    def test_package_validator_rejects_files_outside_allowlist(self):
        with tempfile.TemporaryDirectory() as td:
            package = Path(td) / "extra.zip"
            build_skill_package(ROOT, package)
            with zipfile.ZipFile(package, "a") as archive:
                archive.writestr("workflow-builder/evals/prompt-injection.json", "{}")
            errors = validate_package(package)
            self.assertTrue(any("白名单外文件" in error for error in errors))

    def test_build_rejects_symlinked_runtime_file(self):
        with tempfile.TemporaryDirectory() as td:
            copied = Path(td) / "source"
            copied.mkdir()
            for relative in (Path("plugin.json"), *RUNTIME_FILES):
                target = copied / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((ROOT / relative).read_bytes())
            target_file = copied / "assets/workflow-card.template.md"
            with patch("build_plugin.has_symlink_component", side_effect=lambda path, _root: path == target_file):
                with self.assertRaisesRegex(ValueError, "符号链接"):
                    build_skill_package(copied, Path(td) / "blocked.zip")


if __name__ == "__main__":
    unittest.main()
