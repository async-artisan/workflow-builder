#!/usr/bin/env python3
"""Build or verify a content-addressed workflow release manifest."""

import argparse
import json
import sys
from pathlib import Path

from release_utils import compute_release_id, sha256_file


def build_release(base_dir, inputs):
    base = base_dir.resolve()
    files = []
    for source in inputs:
        path = source.resolve()
        if not path.is_file():
            raise ValueError(f"输入不是可读取文件：{source}")
        try:
            relative = path.relative_to(base).as_posix()
        except ValueError as exc:
            raise ValueError(f"输入必须位于 base-dir 内：{source}") from exc
        files.append({"path": relative, "sha256": sha256_file(path)})
    files.sort(key=lambda item: item["path"])
    return {"release_id": compute_release_id(files), "files": files}


def verify_release(base_dir, release_path):
    release = json.loads(release_path.read_text(encoding="utf-8-sig"))
    expected = build_release(
        base_dir,
        [base_dir / item["path"] for item in release.get("files", [])],
    )
    errors = []
    if expected["files"] != release.get("files"):
        errors.append("文件内容或路径摘要已变化。")
    if expected["release_id"] != release.get("release_id"):
        errors.append("release_id 与当前文件摘要不匹配。")
    return errors


def main():
    parser = argparse.ArgumentParser(description="生成或验证内容绑定的 workflow release。")
    parser.add_argument("inputs", nargs="*", type=Path, help="纳入发布的 SOP、Skill、适配器或快照文件")
    parser.add_argument("--base-dir", type=Path, default=Path.cwd(), help="相对路径根目录")
    parser.add_argument("--output", type=Path, help="release JSON 输出路径")
    parser.add_argument("--check", type=Path, help="验证已有 release JSON 是否发生漂移")
    parser.add_argument("--force", action="store_true", help="允许覆盖已有输出文件")
    args = parser.parse_args()
    try:
        if args.check:
            if args.inputs:
                raise ValueError("--check 模式不需要输入文件。")
            errors = verify_release(args.base_dir, args.check)
            for error in errors:
                print(f"ERROR: {error}")
            print("Release is unchanged." if not errors else "Release drift detected.")
            return 0 if not errors else 2
        if not args.inputs:
            raise ValueError("至少提供一个纳入发布的文件。")
        release = build_release(args.base_dir, args.inputs)
        content = json.dumps(release, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            if args.output.exists() and not args.force:
                raise ValueError(f"输出已存在：{args.output}；确认覆盖时使用 --force。")
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(content, encoding="utf-8")
        else:
            print(content, end="")
        print(f"Release built: {release['release_id']}", file=sys.stderr)
        return 0
    except (OSError, UnicodeError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"Release build/check failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
