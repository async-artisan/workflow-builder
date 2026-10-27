#!/usr/bin/env python3
"""Build and validate a portable Agent Plugins 1.0 package."""

import argparse
import json
import re
import stat
import sys
import zipfile
from pathlib import Path

SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
ALLOWED_FIELDS = {
    "$schema", "name", "version", "description", "author", "homepage",
    "repository", "license", "keywords", "extensions",
}
SKILL_NAME = "workflow-builder"
PLUGIN_SKILL_PREFIX = Path("skills") / SKILL_NAME
SKILL_PACKAGE_PREFIX = Path(SKILL_NAME)
RUNTIME_FILES = tuple(
    Path(item)
    for item in (
        "SKILL.md",
        "LICENSE",
        "assets/capability-card.template.md",
        "assets/discovery-brief.template.md",
        "assets/run-manifest.template.json",
        "assets/sop.template.md",
        "assets/verification-signoff.template.md",
        "assets/workflow-card.template.md",
        "references/capability-composition.md",
        "references/discovery-interview.md",
        "references/evaluation.md",
        "references/knowledge-base.md",
        "references/platform-adapters.md",
        "references/release-binding.md",
        "references/risk-and-budgets.md",
        "references/run-manifest.md",
        "references/sop-format.md",
        "references/workflow-method.md",
        "scripts/build_release.py",
        "scripts/release_utils.py",
        "scripts/sop_to_skill.py",
        "scripts/validate_run.py",
    )
)
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
    return sorted(RUNTIME_FILES, key=lambda item: item.as_posix())


def has_symlink_component(path, root):
    path = path.absolute()
    root = root.absolute()
    current = path
    while True:
        if current.is_symlink():
            return True
        if current == root:
            return False
        parent = current.parent
        if parent == current:
            return False
        current = parent


def validate_source(root):
    root = Path(root)
    manifest_path = root / "plugin.json"
    if has_symlink_component(manifest_path, root):
        raise ValueError("拒绝通过符号链接读取 plugin.json。")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    errors = validate_manifest(manifest)
    files = skill_files(root)
    for relative in files:
        path = root / relative
        if has_symlink_component(path, root):
            errors.append(f"发布文件不能是符号链接：{relative.as_posix()}")
        elif not path.is_file():
            errors.append(f"发布白名单文件缺失：{relative.as_posix()}")
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
                zip_info(PLUGIN_SKILL_PREFIX / relative),
                (root / relative).read_bytes(),
            )
    return manifest, len(files) + 1


def build_skill_package(root, output):
    manifest, files, errors = validate_source(root)
    if errors:
        raise ValueError("\n".join(errors))
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w") as archive:
        for relative in files:
            archive.writestr(
                zip_info(SKILL_PACKAGE_PREFIX / relative),
                (root / relative).read_bytes(),
            )
    return manifest, len(files)


def validate_package(path):
    errors = []
    with zipfile.ZipFile(path) as archive:
        listed_names = archive.namelist()
        names = set(listed_names)
        if len(listed_names) != len(names):
            errors.append("ZIP 包含重复路径。")
        if archive.testzip() is not None:
            errors.append("ZIP 内容损坏。")
        is_plugin_package = "plugin.json" in names
        prefix = PLUGIN_SKILL_PREFIX if is_plugin_package else SKILL_PACKAGE_PREFIX
        expected_names = {
            (prefix / relative).as_posix() for relative in RUNTIME_FILES
        }
        if is_plugin_package:
            expected_names.add("plugin.json")
        for name in sorted(expected_names - names):
            errors.append(f"ZIP 缺少发布文件：{name}")
        for name in sorted(names - expected_names):
            errors.append(f"ZIP 含有白名单外文件：{name}")
        for info in archive.infolist():
            name = info.filename
            if (
                name.startswith("/")
                or chr(92) in name
                or re.match(r"^[A-Za-z]:", name)
                or ".." in Path(name).parts
            ):
                errors.append(f"ZIP 路径不安全：{name}")
            mode = info.external_attr >> 16
            if stat.S_IFMT(mode) and not stat.S_ISREG(mode):
                errors.append(f"ZIP 中只允许普通文件：{name}")
        if not errors and is_plugin_package:
            manifest = json.loads(archive.read("plugin.json").decode("utf-8"))
            errors.extend(validate_manifest(manifest))
        if not is_plugin_package and "workflow-builder/SKILL.md" not in names:
            errors.append("ZIP 缺少 workflow-builder/SKILL.md。")
    return errors


def main():
    parser = argparse.ArgumentParser(description="构建或验证 Agent Skill 与 Agent Plugins ZIP。")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, help="插件 ZIP 输出路径")
    parser.add_argument("--format", choices=("plugin", "skill"), default="plugin", help="构建插件包或直接安装的 Skill ZIP")
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
            with zipfile.ZipFile(args.validate_zip) as archive:
                package_type = "Agent Plugins" if "plugin.json" in archive.namelist() else "Direct Skill"
            print(f"{package_type} package is valid: {args.validate_zip}")
            return 0
        if args.check:
            print("Agent Plugins source is valid.")
            return 0
        manifest, _files, _errors = validate_source(args.root)
        if args.format == "skill":
            default_name = f"{SKILL_NAME}-v{manifest['version']}.zip"
        else:
            default_name = f"{manifest['name']}-v{manifest['version']}-plugin.zip"
        output = args.output or args.root / "dist" / default_name
        if output.exists() and not args.force:
            raise ValueError(f"输出已存在：{output}；确认覆盖时使用 --force。")
        builder = build_skill_package if args.format == "skill" else build_package
        _manifest, count = builder(args.root, output)
        zip_errors = validate_package(output)
        if zip_errors:
            raise ValueError("\n".join(zip_errors))
        label = "Direct Skill" if args.format == "skill" else "Agent Plugins"
        print(f"{label} package built: {output}")
        print(f"Packaged files: {count}; platform review remains independent.")
        return 0
    except (OSError, UnicodeError, ValueError, KeyError, TypeError, json.JSONDecodeError, zipfile.BadZipFile) as exc:
        print(f"Agent Plugins build/check failed:\n{exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
