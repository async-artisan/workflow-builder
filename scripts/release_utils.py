"""Shared release digest helpers for workflow-builder tools."""

import hashlib
import json

DIGEST_PREFIX = "sha256:"


def sha256_bytes(content):
    return hashlib.sha256(content).hexdigest()


def sha256_file(path):
    return sha256_bytes(path.read_bytes())


def compute_release_id(files):
    canonical = sorted(
        ({"path": item["path"], "sha256": item["sha256"]} for item in files),
        key=lambda item: item["path"],
    )
    payload = json.dumps(canonical, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return DIGEST_PREFIX + sha256_bytes(payload)


def is_sha256(value):
    if not isinstance(value, str) or len(value) != 64:
        return False
    return all(char in "0123456789abcdef" for char in value.lower())
