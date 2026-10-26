#!/usr/bin/env python3
"""Validate workflow run evidence and derive lifecycle status from it."""

import argparse
import json
import sys
from pathlib import Path

from release_utils import compute_release_id, is_sha256

STEP_STATES = {"pending", "running", "completed", "failed", "skipped", "blocked"}
RUN_STATES = {"in_progress", "completed", "failed", "blocked", "budget_exhausted"}
MODES = {"design", "trial", "live", "reuse", "handoff"}
RISK_TIERS = {"read_only", "reversible_write", "restricted_write"}
SIDE_EFFECTS = {"none", "read", "reversible_write", "restricted_write"}
EXTERNAL_STATES = {"not_attempted", "succeeded", "unknown", "reconciled"}
CHECK_STATES = {"not_run", "passed", "failed", "not_applicable"}
STATUS_NAMES = ("designed", "tested", "human_approved", "reuse_validated", "handoff_validated")


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def valid_quote(value):
    if not nonempty(value):
        return False
    return value.strip().lower() not in {"...", "pending", "n/a", "待签核", "待人工反馈"}


def valid_approval(approval, release_id):
    return (
        approval.get("decision") in {"approved", "conditional"}
        and nonempty(approval.get("approver"))
        and valid_quote(approval.get("quote"))
        and approval.get("release_id") == release_id
        and nonempty(approval.get("scope"))
        and nonempty(approval.get("evidence"))
    )


def validate_manifest(data):
    errors = []
    release = data.get("release", {})
    files = release.get("files", [])
    release_id = release.get("release_id")
    release_valid = bool(files) and all(
        nonempty(item.get("path")) and is_sha256(item.get("sha256")) for item in files
    )
    if not release_valid:
        errors.append("release.files 至少需要一项有效路径和 SHA-256 摘要。")
    elif compute_release_id(files) != release_id:
        release_valid = False
        errors.append("release_id 与文件摘要不匹配。")

    workflow = data.get("workflow", {})
    designed = release_valid and nonempty(workflow.get("name")) and nonempty(workflow.get("version"))
    if not designed:
        errors.append("designed 需要有效 release、工作流名称和版本。")

    approvals = data.get("approvals", [])
    human_approved = any(valid_approval(item, release_id) for item in approvals)
    for index, approval in enumerate(approvals):
        if approval.get("decision") in {"approved", "conditional"} and not valid_approval(approval, release_id):
            errors.append(f"approvals[{index}] 缺少有效人员、原话、范围、证据或匹配的 release_id。")

    if data.get("risk_tier") not in RISK_TIERS:
        errors.append("risk_tier 无效。")

    steps = data.get("steps", [])
    completed = []
    valid_completed = []
    has_restricted_effect = False
    for index, step in enumerate(steps):
        label = step.get("step_id") or f"steps[{index}]"
        state = step.get("state")
        if not nonempty(step.get("step_id")):
            errors.append(f"steps[{index}] 缺少 step_id。")
        if state not in STEP_STATES:
            errors.append(f"{label} 的 state 无效。")
        if not isinstance(step.get("attempt"), int) or step.get("attempt") < 0:
            errors.append(f"{label} 的 attempt 必须是非负整数。")
        effect = step.get("side_effect")
        if effect not in SIDE_EFFECTS:
            errors.append(f"{label} 的 side_effect 无效。")
        if data.get("risk_tier") == "read_only" and effect in {"reversible_write", "restricted_write"}:
            errors.append(f"{label} 在 read_only 档位中包含写入副作用。")
        if data.get("risk_tier") == "reversible_write" and effect == "restricted_write":
            errors.append(f"{label} 超出 reversible_write 档位。")
        if state == "completed":
            completed.append(step)
            complete_valid = True
            if step.get("attempt", 0) < 1:
                complete_valid = False
            if not is_sha256(step.get("input_digest")) or not is_sha256(step.get("output_digest")):
                errors.append(f"{label} 已完成但缺少有效输入或输出摘要。")
                complete_valid = False
            if not step.get("evidence"):
                errors.append(f"{label} 已完成但缺少检查证据。")
                complete_valid = False
            if complete_valid:
                valid_completed.append(step)
        if effect in {"reversible_write", "restricted_write"}:
            if not nonempty(step.get("side_effect_intent")):
                errors.append(f"{label} 缺少 side_effect_intent。")
            if not nonempty(step.get("idempotency_key")) and not nonempty(step.get("recovery")):
                errors.append(f"{label} 需要幂等键或恢复/补偿方式。")
            external_state = step.get("external_state")
            if external_state not in EXTERNAL_STATES:
                errors.append(f"{label} 的 external_state 无效。")
            if state == "completed" and (
                external_state not in {"succeeded", "reconciled"} or not nonempty(step.get("external_receipt"))
            ):
                errors.append(f"{label} 写入完成但缺少成功状态与外部回执。")
            if external_state == "unknown" and (state == "completed" or step.get("attempt", 0) > 1):
                errors.append(f"{label} 外部结果未知，禁止直接完成或重试。")
            if external_state == "reconciled" and not nonempty(step.get("external_receipt")):
                errors.append(f"{label} 对账后仍缺少外部回执。")
        if effect == "restricted_write":
            if state == "completed" or step.get("external_state") != "not_attempted":
                has_restricted_effect = True
            if state == "completed" and not human_approved:
                errors.append(f"{label} 缺少绑定当前 release 的人工批准。")

    if has_restricted_effect and not nonempty(data.get("dry_run_evidence")):
        errors.append("restricted_write 需要受控试跑证据 dry_run_evidence。")

    checks = data.get("checks", [])
    critical_checks = [item for item in checks if item.get("critical") is True]
    for index, check in enumerate(checks):
        if check.get("state") not in CHECK_STATES:
            errors.append(f"checks[{index}] 的 state 无效。")
        if check.get("state") == "passed" and not nonempty(check.get("evidence")):
            errors.append(f"checks[{index}] 通过但缺少证据。")
    critical_passed = bool(critical_checks) and all(item.get("state") == "passed" for item in critical_checks)

    mode = data.get("mode")
    if mode not in MODES:
        errors.append("mode 无效。")
    tested = (
        mode in {"trial", "live", "reuse", "handoff"}
        and is_sha256(data.get("input", {}).get("digest"))
        and bool(completed)
        and len(completed) == len(valid_completed)
    )

    evaluation = data.get("evaluation", {})
    reuse_validated = (
        tested
        and nonempty(evaluation.get("case_id"))
        and nonempty(evaluation.get("baseline_id"))
        and evaluation.get("distinct_from_tuning") is True
        and evaluation.get("threshold_met") is True
        and critical_passed
    )

    handoff = data.get("handoff", {})
    handoff_validated = (
        handoff.get("independent_session") is True
        and handoff.get("entry_verified") is True
        and handoff.get("continue_verified") is True
        and nonempty(handoff.get("evidence"))
    )

    budget = data.get("budget", {})
    for actual, maximum in (("actual_tool_calls", "max_tool_calls"), ("actual_minutes", "max_minutes"), ("actual_cost", "max_cost")):
        if actual in budget and maximum in budget:
            if not isinstance(budget[actual], (int, float)) or not isinstance(budget[maximum], (int, float)):
                errors.append(f"budget.{actual} 与 {maximum} 必须是数值。")
            elif budget[actual] > budget[maximum] and data.get("run_state") != "budget_exhausted":
                errors.append(f"budget.{actual} 已超过上限，run_state 必须为 budget_exhausted。")
    max_attempt = max((step.get("attempt", 0) for step in steps), default=0)
    if "max_attempts" in budget and max_attempt > budget["max_attempts"] and data.get("run_state") != "budget_exhausted":
        errors.append("步骤尝试次数超过预算，run_state 必须为 budget_exhausted。")
    if data.get("run_state") not in RUN_STATES:
        errors.append("run_state 无效。")
    if data.get("run_state") == "completed" and not critical_passed:
        errors.append("run_state=completed 要求所有关键检查通过。")

    derived = {
        "designed": designed,
        "tested": tested,
        "human_approved": human_approved,
        "reuse_validated": reuse_validated,
        "handoff_validated": handoff_validated,
    }
    declared = data.get("declared_status", {})
    for name in STATUS_NAMES:
        if declared.get(name) is not derived[name]:
            errors.append(f"declared_status.{name} 与证据推导值 {derived[name]} 不一致。")
    return derived, errors


def main():
    parser = argparse.ArgumentParser(description="校验运行清单，并从证据推导工作流状态。")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--json", action="store_true", help="输出机器可读结果")
    args = parser.parse_args()
    try:
        data = json.loads(args.manifest.read_text(encoding="utf-8-sig"))
        derived, errors = validate_manifest(data)
    except (OSError, UnicodeError, json.JSONDecodeError, AttributeError, TypeError) as exc:
        print(f"运行清单无法解析：{exc}", file=sys.stderr)
        return 2
    result = {"valid": not errors, "derived_status": derived, "errors": errors}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for name, value in derived.items():
            print(f"{name}: {value}")
        for error in errors:
            print(f"ERROR: {error}")
        print("Run manifest is valid." if not errors else "Run manifest is invalid.")
    return 0 if not errors else 2


if __name__ == "__main__":
    sys.exit(main())
