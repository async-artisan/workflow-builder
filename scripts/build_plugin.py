#!/usr/bin/env python3
"""Build and validate a portable Agent Plugins 1.0 package."""

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path

SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
ALLOWED_FIELDS = {
    "$schema", "name", "version", "description", "author", "homepage",
    "repository", "license", "keywords", "extensions",
}
IGNORED_DIRS = {".git", ".github", "__pycache__", "build", "dist", "course-workflow-builder"}
NAME_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")


def validate_manifest(manifest):
    errors = []
    unknown = set(manifest) - ALLOWED_FIELDS
    if unknown:
        errors.append(f"未知顶层字段：{', '.join(sorted(unknown))}")
    if manifest.get("$schema") != SCHEMA:
        errors.append("$schema 必须是 Agent Plugins 1.0 规范地址。")
    if not isinstance(manifest.get("name"), str) or not NAME_PATTERN.fullmatch(manifest["name"]):
        errors.append("name 必须是小写连字符标识。")
    if not isinstance(manifest.get("version"), str) or not VERSION_PATTERN.fullmatch(manifest["version"]):
        errors.append("version 必须是语义化版本。")
    if not isinstance(manifest.get("description"), str) or not manifest["description"].strip():
        errors.append("description 不能为空。")
    author = manifest.get("author", {})
    if not isinstance(author, dict) or not author.get("name"):
        errors.append("author.name 不能为空。")
    for label, url in (
        ("homepage", manifest.get("homepage")),
        ("repository", manifest.get("repository")),
        ("author.url", author.get("url") if isinstance(author, dict) else None),
    ):
        if not isinstance(url, str) or not url.startswith("https://"):
            errors.append(f"{label} 必须是 HTTPS URL。")
    if not manifest.get("license"):
        errors.append("license 不能为空。")
    keywords = manifest.get("keywords")
    if not isinstance(keywords, list) or not keywords or not all(isinstance(item, str) and item.strip() for item in keywords):
        errors.append("keywords 必须是非空字符串数组。")
    return errors


def skill_files(root):
    files = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if any(part in IGNORED_DIRS for part in relative.parts):
            continue
        if relative.as_posix() == "plugin.json" or path.suffix == ".pyc":
            continue
        files.append(relative)
    return sorted(files, key=lambda item: item.as_posix())


def validate_source(root):
    manifest = json.loads((root / "plugin.json").read_text(encoding="utf-8"))
    errors = validate_manifest(manifest)
    files = skill_files(root)
    if Path("SKILL.md") not in files:
        errors.append("根目录缺少 SKILL.md。")
    return manifest, files, errors


def zip_info(path):
    info = zipfile.ZipInfo(path.as_posix(), date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    return info


def build_package(root, output):
    manifest, files, errors = validate_source(root)
    if errors:
        raise ValueError("\n".join(errors))
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr(zip_info(Path("plugin.json")), (root / "plugin.json").read_bytes())
        for relative in files:
            archive.writestr(
                zip_info(Path("skills/workflow-builder") / relative),
                (root / relative).read_bytes(),
            )
    return manifest, len(files) + 1


def validate_package(path):
    errors = []
    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
        if archive.testzip() is not None:
            errors.append("ZIP 内容损坏。")
        if "plugin.json" not in names:
            errors.append("ZIP 根目录缺少 plugin.json。")
        if "skills/workflow-builder/SKILL.md" not in names:
            errors.append("ZIP 缺少 skills/workflow-builder/SKILL.md。")
        if "SKILL.md" in names:
            errors.append("插件根目录不应直接包含 SKILL.md。")
        for name in names:
            if name.startswith("/") or ".." in Path(name).parts:
                errors.append(f"ZIP 路径不安全：{name}")
            if "/.git/" in name or name.startswith(".git/"):
                errors.append("ZIP 不应包含 .git。")
        if not errors:
            manifest = json.loads(archive.read("plugin.json").decode("utf-8"))
            errors.extend(validate_manifest(manifest))
    return errors


def main():
    parser = argparse.ArgumentParser(description="构建或验证 Agent Plugins 1.0 ZIP。")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, help="插件 ZIP 输出路径")
    parser.add_argument("--check", action="store_true", help="只验证源码，不写文件")
    parser.add_argument("--validate-zip", type=Path, help="验证已有插件 ZIP")
    parser.add_argument("--force", action="store_true", help="允许覆盖已有 ZIP")
    args = parser.parse_args()
    try:
        if args.validate_zip:
            errors = validate_package(args.validate_zip)
        else:
            _manifest, _files, errors = validate_source(args.root)
        if errors:
            raise ValueError("\n".join(errors))
        if args.validate_zip:
            print(f"Agent Plugins package is valid: {args.validate_zip}")
            return 0
        if args.check:
            print("Agent Plugins source is valid.")
            return 0
        manifest, _files, _errors = validate_source(args.root)
        output = args.output or args.root / "dist" / f"{manifest['name']}-v{manifest['version']}-plugin.zip"
        if output.exists() and not args.force:
            raise ValueError(f"输出已存在：{output}；确认覆盖时使用 --force。")
        _manifest, count = build_package(args.root, output)
        zip_errors = validate_package(output)
        if zip_errors:
            raise ValueError("\n".join(zip_errors))
        print(f"Agent Plugins package built: {output}")
        print(f"Packaged files: {count}; official portal validation remains pending.")
        return 0
    except (OSError, UnicodeError, ValueError, KeyError, TypeError, json.JSONDecodeError, zipfile.BadZipFile) as exc:
        print(f"Agent Plugins build/check failed:\n{exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
