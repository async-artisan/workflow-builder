#!/usr/bin/env python3
"""Run dependency-free structural checks for the workflow-builder repository."""

import ast
import json
import re
import sys
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[1]
    errors = []
    skill = (root / "SKILL.md").read_text(encoding="utf-8")
    if not skill.startswith("---\n") or "\n---\n" not in skill[4:]:
        errors.append("SKILL.md frontmatter 缺失。")
    for field in ("name", "description"):
        if not re.search(rf"(?m)^{field}:\s*\S+", skill):
            errors.append(f"SKILL.md 缺少 {field}。")

    for path in root.rglob("*.md"):
        if ".git" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        for target in re.findall(r"\[[^]]+\]\(([^)]+)\)", text):
            if "://" in target or target.startswith(("#", "mailto:")):
                continue
            clean = target.split("#")[0]
            if clean and not (path.parent / clean).resolve().exists():
                errors.append(f"{path.relative_to(root)} 的链接不存在：{target}")

    for path in root.rglob("*.json"):
        if ".git" in path.parts:
            continue
        try:
            json.loads(path.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError as exc:
            errors.append(f"{path.relative_to(root)} JSON 无效：{exc}")

    for path in list((root / "scripts").glob("*.py")) + list((root / "tests").glob("*.py")):
        try:
            ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError as exc:
            errors.append(f"{path.relative_to(root)} Python 语法无效：{exc}")

    for error in errors:
        print(f"ERROR: {error}")
    print("Repository checks passed." if not errors else "Repository checks failed.")
    return 0 if not errors else 2


if __name__ == "__main__":
    sys.exit(main())
