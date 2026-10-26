#!/usr/bin/env python3
"""Validate a parameterized SOP and generate an Agent Skill from it."""

import argparse
import json
import re
import sys
from pathlib import Path

REQUIRED_FRONTMATTER = ("name", "description", "version")
REQUIRED_SECTIONS = (
    "Overview",
    "Parameters",
    "Inputs",
    "Steps",
    "Human Gates",
    "Outputs",
    "Validation",
    "Troubleshooting",
)
PARAMETER_HEADER = ["name", "type", "required", "default", "description"]
VALID_TYPES = {"string", "text", "integer", "number", "boolean", "enum", "path", "json"}
NAME_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
PARAMETER_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


def parse_scalar(value):
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] == '"':
        return json.loads(value)
    if len(value) >= 2 and value[0] == value[-1] == "'":
        return value[1:-1].replace("''", "'")
    return value


def parse_parameter_rows(body, errors):
    match = re.search(
        r"(?ms)^##\s+Parameters\s*$\n(.*?)(?=^##\s+|\Z)", body
    )
    if not match:
        return []

    rows = []
    seen_header = False
    for line in match.group(1).splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if cells and cells[0].lower() == "name":
            seen_header = True
            if [cell.lower() for cell in cells] != PARAMETER_HEADER:
                errors.append("Parameters 表头必须为 Name / Type / Required / Default / Description。")
            continue
        if cells and all("-" in cell and set(cell) <= set("-: ") for cell in cells):
            continue
        if len(cells) != 5:
            errors.append(f"参数表行列数无效：{stripped}")
            continue
        rows.append(cells)

    if not seen_header:
        errors.append("Parameters 章节缺少参数表头。")
    if not rows:
        errors.append("Parameters 章节至少需要一个参数；无参数流程也应定义 task_name 或等效运行入口。")

    seen_names = set()
    for name, param_type, required, _default, _description in rows:
        if not PARAMETER_PATTERN.fullmatch(name):
            errors.append(f"参数名必须使用 snake_case：{name or '<empty>'}")
        if name in seen_names:
            errors.append(f"参数名重复：{name}")
        seen_names.add(name)
        if param_type not in VALID_TYPES:
            errors.append(f"参数 {name} 的类型无效：{param_type}")
        if required not in {"yes", "no"}:
            errors.append(f"参数 {name} 的 Required 必须为 yes 或 no。")
    return rows


def parse_sop(text):
    lines = text.splitlines()
    errors = []
    if not lines or lines[0].strip() != "---":
        raise ValueError("SOP 必须以 YAML frontmatter 开始。")

    try:
        end = next(index for index in range(1, len(lines)) if lines[index].strip() == "---")
    except StopIteration as exc:
        raise ValueError("YAML frontmatter 缺少结束分隔线。") from exc

    frontmatter = {}
    for line_number in range(1, end):
        stripped = lines[line_number].strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" not in stripped:
            errors.append(f"frontmatter 第 {line_number + 1} 行缺少冒号。")
            continue
        key, raw_value = stripped.split(":", 1)
        key = key.strip()
        if key in frontmatter:
            errors.append(f"frontmatter 字段重复：{key}")
            continue
        try:
            frontmatter[key] = parse_scalar(raw_value)
        except (ValueError, json.JSONDecodeError) as exc:
            errors.append(f"frontmatter 字段 {key} 无法解析：{exc}")

    body = "\n".join(lines[end + 1 :]).strip() + "\n"
    for key in REQUIRED_FRONTMATTER:
        if not str(frontmatter.get(key, "")).strip():
            errors.append(f"frontmatter 缺少必填字段：{key}")

    name = str(frontmatter.get("name", ""))
    if name and not NAME_PATTERN.fullmatch(name):
        errors.append("name 必须以小写字母开头，且只包含小写字母、数字和单个连字符。")

    for section in REQUIRED_SECTIONS:
        if not re.search(rf"(?m)^##\s+{re.escape(section)}\s*$", body):
            errors.append(f"缺少必需章节：## {section}")

    parameters = parse_parameter_rows(body, errors)
    if errors:
        raise ValueError("\n".join(f"- {error}" for error in errors))
    return frontmatter, body, parameters


def render_skill(frontmatter, body):
    description = json.dumps(str(frontmatter["description"]), ensure_ascii=False)
    return (
        "---\n"
        f"name: {frontmatter['name']}\n"
        f"description: {description}\n"
        "---\n\n"
        f"<!-- Generated from SOP version {frontmatter['version']}. "
        "Edit the SOP source before regenerating. -->\n\n"
        f"{body}"
    )


def main():
    parser = argparse.ArgumentParser(description="验证参数化 SOP，并生成 Agent Skill。")
    parser.add_argument("source", type=Path, help=".sop.md 文件路径")
    parser.add_argument("--output-dir", type=Path, help="Skill 输出根目录")
    parser.add_argument("--check", action="store_true", help="只验证，不写文件")
    parser.add_argument("--force", action="store_true", help="允许覆盖已生成的同名 SKILL.md")
    args = parser.parse_args()

    if not args.check and args.output_dir is None:
        parser.error("生成 Skill 时必须提供 --output-dir；只验证请使用 --check。")

    try:
        text = args.source.expanduser().read_text(encoding="utf-8-sig")
        frontmatter, body, parameters = parse_sop(text)
        name = frontmatter["name"]
        if args.check:
            print(f"SOP valid: {name}; parameters: {len(parameters)}")
            return 0

        output_root = args.output_dir.expanduser().resolve()
        skill_path = output_root / name / "SKILL.md"
        if skill_path.exists() and not args.force:
            raise ValueError(f"目标已存在：{skill_path}；确认覆盖时才使用 --force。")
        skill_path.parent.mkdir(parents=True, exist_ok=True)
        skill_path.write_text(render_skill(frontmatter, body), encoding="utf-8")
        print(f"Skill generated: {skill_path}")
        print("Status: generated; loading and runtime behavior remain unverified.")
        return 0
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"SOP validation/generation failed:\n{exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
