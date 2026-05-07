#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STAGE_ORDER = ["onboarding", "interview", "seed-prd", "research", "design", "r-and-d", "dev", "eval"]
STAGE_SOURCE_FILES: dict[str, list[str]] = {
    "onboarding": [
        ".codex-loop/workflow/ONBOARDING.md",
        ".codex-loop/workflow/PROFILE.md",
        ".codex-loop/workflow/STATUS.md",
    ],
    "interview": [
        ".codex-loop/intake/ANSWERS.md",
        ".codex-loop/intake/APPROVAL.md",
        ".codex-loop/context/open-questions.json",
    ],
    "seed-prd": [
        ".codex-loop/prd/PRD.md",
        ".codex-loop/prd/SUMMARY.md",
        ".codex-loop/tasks.json",
    ],
    "research": [
        ".codex-loop/research/PLAN.md",
        ".codex-loop/research/FINDINGS.md",
        ".codex-loop/research/APPROVAL.md",
    ],
    "design": [
        ".codex-loop/design/DESIGN.md",
        ".codex-loop/assets/registry.json",
    ],
    "r-and-d": [
        ".codex-loop/research/FINDINGS.md",
        ".codex-loop/prd/PRD.md",
        ".codex-loop/tasks.json",
    ],
    "dev": [
        ".codex-loop/tasks.json",
        ".codex-loop/logs/LOG.md",
        ".codex-loop/history/seed-worker.log",
    ],
    "eval": [
        ".codex-loop/evals",
        ".codex-loop/reviews",
        ".codex-loop/state.json",
    ],
}
DEFAULT_SPEC: dict[str, Any] = {
    "version": 1,
    "decisionMode": "automatic",
    "retryLimit": 2,
    "stages": STAGE_ORDER,
    "thresholds": {
        "onboarding": 0.85,
        "interview": 0.85,
        "seed-prd": 0.85,
        "research": 0.85,
        "design": 0.85,
        "r-and-d": 0.85,
        "dev": 0.90,
        "eval": 0.90,
    },
    "issueAllowances": {
        "default": {"critical": 0, "high": 0, "medium": 0},
        "research": {"critical": 0, "high": 0, "medium": 2},
        "r-and-d": {"critical": 0, "high": 0, "medium": 2},
        "design": {"critical": 0, "high": 0, "medium": 1},
        "dev": {"critical": 0, "high": 0, "medium": 1},
        "eval": {"critical": 0, "high": 0, "medium": 1},
    },
    "hardFailConditions": [
        "missing_required_user_approval",
        "test_failure",
        "evidence_free_core_decision",
        "missing_requirement_mapping",
    ],
    "rollbackRoutes": {
        "missing_requirement_mapping": "interview_or_seed_prd",
        "missing_required_user_approval": "user_judgment_gate",
        "evidence_free_core_decision": "research",
        "evidence_gap": "research",
        "design_quality_below_threshold": "design_remediation_then_user_judgment",
        "conflicting_user_goals": "user_judgment_gate",
        "tool_or_api_limit": "r-and-d",
        "implementation_feasibility": "r-and-d_or_dev_planning",
        "missing_schema_or_artifact": "same_stage_remediation",
        "test_failure": "dev",
        "score_below_threshold": "same_stage_remediation",
        "issue_allowance_exceeded": "same_stage_remediation",
        "missing_residual_risk": "same_stage_remediation",
    },
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def state_dir_from(root: Path) -> Path:
    return root if root.name == ".codex-loop" else root / ".codex-loop"


def project_root_from_state(state_dir: Path) -> Path:
    return state_dir.parent if state_dir.name == ".codex-loop" else state_dir


def stage_gate_dir(state_dir: Path) -> Path:
    return state_dir / "stage-gates"


def spec_path(state_dir: Path) -> Path:
    return stage_gate_dir(state_dir) / "spec.json"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_text(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace").strip()


def ensure_stage_gate_files(state_dir: Path) -> None:
    gates_dir = stage_gate_dir(state_dir)
    (gates_dir / "artifacts").mkdir(parents=True, exist_ok=True)
    (gates_dir / "results").mkdir(parents=True, exist_ok=True)
    if not spec_path(state_dir).exists():
        write_json(spec_path(state_dir), DEFAULT_SPEC)


def has_placeholder_text(text: str) -> bool:
    lowered = (text or "").lower()
    placeholders = [
        "대기 중",
        "작성 필요",
        "아직",
        "todo",
        "tbd",
        "placeholder",
        "pending",
    ]
    return any(item in lowered for item in placeholders)


def first_nonempty_line(text: str, fallback: str) -> str:
    for raw in (text or "").splitlines():
        line = raw.strip().lstrip("#").strip()
        if line:
            return line[:180]
    return fallback


def collect_source_evidence(project_root: Path, stage: str) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    evidence: list[dict[str, Any]] = []
    issues: list[dict[str, str]] = []
    for index, rel in enumerate(STAGE_SOURCE_FILES.get(stage, []), start=1):
        path = project_root / rel
        if path.is_dir():
            children = sorted(child for child in path.iterdir() if child.is_file())
            if children:
                evidence.append(
                    {
                        "id": f"EVID-{index:03d}",
                        "type": "directory",
                        "source": rel,
                        "summary": f"{len(children)} files exist for {stage} evidence.",
                    }
                )
            else:
                issues.append({"severity": "medium", "summary": f"No files found in {rel}."})
            continue
        text = read_text(path)
        if not text:
            issues.append({"severity": "medium", "summary": f"Missing or empty evidence file: {rel}."})
            continue
        if has_placeholder_text(text):
            issues.append({"severity": "medium", "summary": f"Evidence file still contains placeholder text: {rel}."})
        evidence.append(
            {
                "id": f"EVID-{index:03d}",
                "type": "file",
                "source": rel,
                "summary": first_nonempty_line(text, rel),
            }
        )
    return evidence, issues


def has_substantive_file(path: Path) -> bool:
    return path.exists() and path.is_file() and bool(read_text(path)) and not has_placeholder_text(read_text(path))


def directory_has_files(path: Path) -> bool:
    return path.exists() and path.is_dir() and any(child.is_file() for child in path.iterdir())


def stage_quality_issues(project_root: Path, stage: str, test_status: bool | None) -> list[dict[str, str]]:
    state_dir = project_root / ".codex-loop"
    issues: list[dict[str, str]] = []
    if stage == "research":
        findings = read_text(state_dir / "research" / "FINDINGS.md")
        plan = read_text(state_dir / "research" / "PLAN.md")
        evidence_markers = ("http://", "https://", "evidence", "source", "근거", "출처")
        if not any(marker in findings.lower() for marker in evidence_markers):
            issues.append({"severity": "high", "summary": "Research findings do not cite concrete evidence or sources."})
        if len(plan.splitlines()) < 8:
            issues.append({"severity": "medium", "summary": "Research plan is too thin for deep research execution."})
    elif stage == "design":
        design = read_text(state_dir / "design" / "DESIGN.md")
        if "reference-pack:" not in design.lower():
            issues.append({"severity": "high", "summary": "Design contract does not select a Reference-Pack."})
        if not directory_has_files(state_dir / "artifacts") and not directory_has_files(state_dir / "assets"):
            issues.append({"severity": "medium", "summary": "Design stage has no visual output, asset, or screenshot artifact."})
    elif stage == "r-and-d":
        findings = read_text(state_dir / "research" / "FINDINGS.md")
        tasks = read_text(state_dir / "tasks.json")
        feasibility_markers = ("feasibility", "spike", "prototype", "tradeoff", "risk", "검증", "실험", "리스크")
        if not any(marker in (findings + tasks).lower() for marker in feasibility_markers):
            issues.append({"severity": "high", "summary": "R&D stage lacks feasibility, spike, tradeoff, or risk evidence."})
    elif stage == "dev":
        if test_status is not True:
            issues.append({"severity": "high", "summary": "Dev stage has no recorded passing test/build/smoke result."})
    elif stage == "eval":
        if test_status is not True:
            issues.append({"severity": "high", "summary": "Eval stage has no recorded passing goal evaluation."})
        if not directory_has_files(state_dir / "evals") and not directory_has_files(state_dir / "reviews"):
            issues.append({"severity": "high", "summary": "Eval stage has no review or evaluation artifact files."})
    elif stage == "seed-prd":
        if not has_substantive_file(state_dir / "prd" / "PRD.md") or not has_substantive_file(state_dir / "prd" / "SUMMARY.md"):
            issues.append({"severity": "high", "summary": "Seed/PRD stage lacks substantive PRD and SUMMARY files."})
    return issues


def infer_requirements(project_root: Path, stage: str, explicit_requirements: list[str] | None = None) -> list[str]:
    if explicit_requirements:
        return [item.strip() for item in explicit_requirements if item.strip()]
    candidates = [
        read_text(project_root / ".codex-loop" / "workflow" / "ONBOARDING.md"),
        read_text(project_root / ".codex-loop" / "prd" / "SUMMARY.md"),
        read_text(project_root / ".codex-loop" / "prd" / "PRD.md"),
        read_text(project_root / ".codex-loop" / "PROMPT.md"),
    ]
    for candidate in candidates:
        line = first_nonempty_line(candidate, "")
        if line and not has_placeholder_text(line):
            return [line]
    return [f"{stage} stage must produce inspectable evidence before passing."]


def stage_approval_required(stage: str) -> bool:
    return stage in {"interview"}


def stage_approval_granted(project_root: Path, stage: str) -> bool:
    if stage == "interview":
        text = read_text(project_root / ".codex-loop" / "intake" / "APPROVAL.md")
        lowered = text.lower()
        return "승인: 예" in text or "approved: yes" in lowered or "status: approved" in lowered or "상태: 승인" in text
    return False


def infer_test_status(project_root: Path, stage: str) -> bool | None:
    if stage not in {"dev", "eval"}:
        return None
    state = project_root / ".codex-loop" / "state.json"
    try:
        payload = json.loads(state.read_text(encoding="utf-8")) if state.exists() else {}
    except json.JSONDecodeError:
        payload = {}
    if payload.get("checksPassed") is False or payload.get("evalPassed") is False:
        return False
    if payload.get("checksPassed") is True or payload.get("evalPassed") is True:
        return True
    return None


def automatic_score(spec: dict[str, Any], stage: str, evidence: list[dict[str, Any]], issues: list[dict[str, str]], approval: dict[str, Any], test_status: bool | None) -> float:
    threshold = stage_threshold(spec, stage)
    if not evidence:
        return 0.0
    if approval.get("required") and not approval.get("granted"):
        return min(0.5, threshold - 0.2)
    if test_status is False:
        return min(0.5, threshold - 0.2)
    if any(issue.get("severity") in {"critical", "high"} for issue in issues):
        return max(0.0, threshold - 0.2)
    medium_count = sum(1 for issue in issues if issue.get("severity") == "medium")
    if medium_count:
        return max(0.0, threshold - 0.05)
    return max(threshold, 0.9)


def generate_stage_artifact(spec: dict[str, Any], project_root: Path, stage: str, requirements: list[str] | None = None) -> dict[str, Any]:
    normalized = normalized_stage(stage)
    evidence, issues = collect_source_evidence(project_root, normalized)
    evidence_id_list = [str(item["id"]) for item in evidence]
    inferred_requirements = infer_requirements(project_root, normalized, requirements)
    requirement_mapping = [
        {
            "requirementId": f"REQ-{index:03d}",
            "summary": requirement,
            "status": "mapped" if evidence_id_list else "missing",
            "evidenceIds": evidence_id_list,
        }
        for index, requirement in enumerate(inferred_requirements, start=1)
    ]
    approval = {
        "required": stage_approval_required(normalized),
        "granted": stage_approval_granted(project_root, normalized),
    }
    test_status = infer_test_status(project_root, normalized)
    issues.extend(stage_quality_issues(project_root, normalized, test_status))
    checks: dict[str, Any] = {}
    if test_status is not None:
        checks["tests"] = {"passed": test_status}
    score = automatic_score(spec, normalized, evidence, issues, approval, test_status)
    residual_risks = [
        {
            "issue": issue["summary"],
            "mitigation": "Resolve or accept explicitly before final completion.",
        }
        for issue in issues
        if issue.get("severity") == "medium"
    ]
    artifact = {
        "stage": normalized,
        "generatedAt": now_iso(),
        "generator": "ralph_stage_gate.py checkpoint",
        "requirementMapping": requirement_mapping,
        "evidence": evidence,
        "coreDecisions": [
            {
                "id": "DEC-001",
                "summary": f"{normalized} stage is ready for automatic gate evaluation.",
                "evidenceIds": evidence_id_list,
            }
        ],
        "score": score,
        "issues": issues,
        "residualRisks": residual_risks,
        "approval": approval,
        "checks": checks,
    }
    return artifact


def load_spec(state_dir: Path) -> dict[str, Any]:
    ensure_stage_gate_files(state_dir)
    return load_json(spec_path(state_dir))


def normalized_stage(stage: str) -> str:
    stage_key = (stage or "").strip().lower().replace("_", "-")
    aliases = {
        "seed": "seed-prd",
        "prd": "seed-prd",
        "seed/prd": "seed-prd",
        "seed-prd": "seed-prd",
        "r&d": "r-and-d",
        "rnd": "r-and-d",
        "rd": "r-and-d",
        "development": "dev",
        "evaluation": "eval",
    }
    return aliases.get(stage_key, stage_key)


def requirement_mapping_coverage(artifact: dict[str, Any]) -> float:
    mappings = artifact.get("requirementMapping", [])
    if not isinstance(mappings, list) or not mappings:
        return 0.0
    mapped = 0
    for item in mappings:
        if not isinstance(item, dict):
            continue
        status = str(item.get("status", "")).lower()
        evidence_ids = item.get("evidenceIds", [])
        if status in {"mapped", "covered", "satisfied"} and isinstance(evidence_ids, list) and evidence_ids:
            mapped += 1
    return mapped / len(mappings)


def evidence_ids(artifact: dict[str, Any]) -> set[str]:
    evidence = artifact.get("evidence", [])
    if not isinstance(evidence, list):
        return set()
    return {str(item.get("id")) for item in evidence if isinstance(item, dict) and item.get("id")}


def count_issues(artifact: dict[str, Any]) -> dict[str, int]:
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    issues = artifact.get("issues", [])
    if not isinstance(issues, list):
        return counts
    for issue in issues:
        if not isinstance(issue, dict):
            continue
        severity = str(issue.get("severity", "")).lower()
        if severity in counts:
            counts[severity] += 1
    return counts


def stage_threshold(spec: dict[str, Any], stage: str) -> float:
    thresholds = spec.get("thresholds", {})
    return float(thresholds.get(stage, thresholds.get("default", 0.85)))


def issue_allowance(spec: dict[str, Any], stage: str) -> dict[str, int]:
    allowances = spec.get("issueAllowances", {})
    merged = {"critical": 0, "high": 0, "medium": 0}
    merged.update(allowances.get("default", {}))
    merged.update(allowances.get(stage, {}))
    return {key: int(merged.get(key, 0)) for key in ("critical", "high", "medium")}


def core_decision_failures(artifact: dict[str, Any], known_evidence: set[str]) -> list[str]:
    failures: list[str] = []
    decisions = artifact.get("coreDecisions", [])
    if not isinstance(decisions, list):
        return failures
    for decision in decisions:
        if not isinstance(decision, dict):
            failures.append("unknown")
            continue
        decision_id = str(decision.get("id") or decision.get("summary") or "unknown")
        refs = decision.get("evidenceIds", [])
        if not isinstance(refs, list) or not refs or not all(str(ref) in known_evidence for ref in refs):
            failures.append(decision_id)
    return failures


def required_approval_missing(artifact: dict[str, Any]) -> bool:
    approval = artifact.get("approval", {})
    if not isinstance(approval, dict):
        return False
    return bool(approval.get("required")) and not bool(approval.get("granted"))


def tests_failed(artifact: dict[str, Any]) -> bool:
    checks = artifact.get("checks", {})
    if not isinstance(checks, dict):
        return False
    tests = checks.get("tests", {})
    if not isinstance(tests, dict):
        return False
    return tests.get("passed") is False


def infer_failure_causes(stage: str, failures: list[str]) -> list[str]:
    causes: list[str] = []
    for failure in failures:
        if failure.startswith("coverage"):
            causes.append("missing_requirement_mapping")
        elif failure.startswith("missing_evidence"):
            causes.append("evidence_gap")
        elif failure.startswith("score"):
            if stage == "design":
                causes.append("design_quality_below_threshold")
            else:
                causes.append("score_below_threshold")
        elif failure.startswith("issue_allowance"):
            causes.append("issue_allowance_exceeded")
        elif failure.startswith("missing_residual_risk"):
            causes.append("missing_residual_risk")
        else:
            causes.append(failure)
    return sorted(set(causes))


def remediation_steps(causes: list[str]) -> list[str]:
    catalog = {
        "missing_requirement_mapping": "Return to the requirement source, add every missing requirement to requirementMapping, and attach evidence IDs before reevaluating.",
        "missing_required_user_approval": "Stop automation and request an explicit user judgment for the blocked approval.",
        "test_failure": "Fix the failing test/build/smoke command, record the passing command output, and rerun the dev/eval gate.",
        "evidence_free_core_decision": "Attach at least one concrete evidence item to every core decision or roll back to research.",
        "evidence_gap": "Run additional research or inspect code/logs until every core claim has evidence.",
        "design_quality_below_threshold": "Revise the design artifact against references, visual outputs, requirements, and implementation feasibility.",
        "score_below_threshold": "Improve the artifact until the stage-specific automatic score threshold is met.",
        "issue_allowance_exceeded": "Resolve critical/high/medium issues until the stage allowance is respected.",
        "missing_residual_risk": "Record every accepted medium issue in residualRisks with owner, mitigation, and expiry.",
        "missing_schema_or_artifact": "Regenerate the artifact as a JSON object following the stage gate schema.",
    }
    return [catalog.get(cause, f"Resolve failure cause: {cause}.") for cause in causes]


def rollback_target(spec: dict[str, Any], causes: list[str], retry_count: int) -> str:
    if not causes:
        return "none"
    routes = spec.get("rollbackRoutes", {})
    if retry_count < int(spec.get("retryLimit", 2)):
        return "same_stage_remediation"
    if "conflicting_user_goals" in causes:
        return routes.get("conflicting_user_goals", "user_judgment_gate")
    if "missing_required_user_approval" in causes:
        return routes.get("missing_required_user_approval", "user_judgment_gate")
    return str(routes.get(causes[0], "user_judgment_gate"))


def previous_retry_count(state_dir: Path, stage: str) -> int:
    result_path = stage_gate_dir(state_dir) / "results" / f"{stage}-latest.json"
    if not result_path.exists():
        return 0
    try:
        result = load_json(result_path)
    except (json.JSONDecodeError, OSError):
        return 0
    if result.get("passed"):
        return 0
    remediation = result.get("remediationPlan", {})
    if not isinstance(remediation, dict):
        return 1
    return int(remediation.get("retryCount", 0) or 0) + 1


def checkpoint_stage(
    spec: dict[str, Any],
    state_dir: Path,
    project_root: Path,
    stage: str,
    requirements: list[str] | None = None,
    retry_count: int = 0,
    artifact_output: Path | None = None,
    result_output: Path | None = None,
) -> tuple[dict[str, Any], dict[str, Any], Path, Path]:
    normalized = normalized_stage(stage)
    artifact = generate_stage_artifact(spec, project_root, normalized, requirements=requirements)
    artifact_path = artifact_output or stage_gate_dir(state_dir) / "artifacts" / f"{normalized}-latest.json"
    write_json(artifact_path, artifact)
    result = evaluate_artifact(spec, artifact, retry_count=retry_count)
    result["artifactPath"] = str(artifact_path)
    output_path = result_output or stage_gate_dir(state_dir) / "results" / f"{normalized}-latest.json"
    write_json(output_path, result)
    return artifact, result, artifact_path, output_path


def stage_slice(spec: dict[str, Any], start: str = "", end: str = "", only: list[str] | None = None) -> list[str]:
    stages = [normalized_stage(stage) for stage in spec.get("stages", STAGE_ORDER)]
    if only:
        requested = [normalized_stage(stage) for stage in only]
        return [stage for stage in stages if stage in requested]
    start_stage = normalized_stage(start) if start else stages[0]
    end_stage = normalized_stage(end) if end else stages[-1]
    if start_stage not in stages:
        raise ValueError(f"Unknown start stage: {start}")
    if end_stage not in stages:
        raise ValueError(f"Unknown end stage: {end}")
    start_index = stages.index(start_stage)
    end_index = stages.index(end_stage)
    if start_index > end_index:
        raise ValueError(f"Start stage must not come after end stage: {start_stage}>{end_stage}")
    return stages[start_index : end_index + 1]


def next_action_for_result(spec: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    if result.get("passed"):
        return {"type": "continue", "reason": "stage_passed"}
    remediation = result.get("remediationPlan", {})
    retry_count = int(remediation.get("retryCount", 0) or 0) if isinstance(remediation, dict) else 0
    retry_limit = int(spec.get("retryLimit", 2))
    rollback = str(result.get("rollbackTarget", "user_judgment_gate"))
    if retry_count < retry_limit and rollback == "same_stage_remediation":
        return {
            "type": "remediate_then_retry",
            "stage": result.get("stage"),
            "retryCount": retry_count,
            "retryLimit": retry_limit,
            "reason": "stage_failed_but_retry_budget_remains",
        }
    if "user_judgment" in rollback:
        return {
            "type": "user_judgment_gate",
            "stage": result.get("stage"),
            "rollbackTarget": rollback,
            "reason": "automation_cannot_safely_continue",
        }
    return {
        "type": "rollback",
        "stage": result.get("stage"),
        "rollbackTarget": rollback,
        "reason": "retry_budget_exhausted_or_previous_stage_required",
    }


def remediation_task_id(stage: str, retry_count: int) -> str:
    safe_stage = normalized_stage(stage).upper().replace("-", "_")
    return f"SG-{safe_stage}-{retry_count + 1:02d}"


def write_remediation_task(state_dir: Path, result: dict[str, Any], next_action: dict[str, Any]) -> Path:
    stage = normalized_stage(str(result.get("stage", "unknown")))
    remediation = result.get("remediationPlan", {})
    retry_count = int(remediation.get("retryCount", 0) or 0) if isinstance(remediation, dict) else 0
    task_id = remediation_task_id(stage, retry_count)
    task_file = f"tasks/TASK-{task_id}.json"
    steps = remediation.get("steps", []) if isinstance(remediation, dict) else []
    causes = result.get("failureCauses", [])
    task_payload = {
        "id": task_id,
        "title": f"Remediate {stage} stage gate failure",
        "status": "blocked" if next_action.get("type") == "user_judgment_gate" else "todo",
        "priority": "p0",
        "summary": f"Resolve {stage} gate failure before Ralph continues.",
        "dependsOn": [],
        "deliverables": [
            f".codex-loop/stage-gates/artifacts/{stage}-latest.json",
            f".codex-loop/stage-gates/results/{stage}-latest.json",
        ],
        "acceptance": [
            f"`python3 scripts/ralph_stage_gate.py checkpoint --stage {stage}` passes.",
            "All hard fail causes are removed or routed to explicit user judgment.",
            "Residual medium risks are recorded with mitigation.",
        ],
        "failureCauses": causes,
        "remediationSteps": steps,
        "nextAction": next_action,
        "source": "ralph-stage-gate",
        "generatedAt": now_iso(),
    }
    task_path = state_dir / task_file
    write_json(task_path, task_payload)

    remediation_path = stage_gate_dir(state_dir) / "remediation" / f"{stage}-latest.json"
    write_json(remediation_path, task_payload)

    tasks_index_path = state_dir / "tasks.json"
    try:
        tasks_index = load_json(tasks_index_path) if tasks_index_path.exists() else {}
    except json.JSONDecodeError:
        tasks_index = {}
    tasks = tasks_index.get("tasks", [])
    if not isinstance(tasks, list):
        tasks = []
    if not any(str(task.get("id")) == task_id for task in tasks if isinstance(task, dict)):
        tasks.append(
            {
                "id": task_id,
                "title": task_payload["title"],
                "status": task_payload["status"],
                "priority": task_payload["priority"],
                "file": task_file,
            }
        )
    tasks_index.update(
        {
            "project": tasks_index.get("project", "SummitHarness Ralph stage-gate remediation"),
            "selection": tasks_index.get("selection", "priority-order"),
            "tasks": tasks,
            "updatedAt": now_iso(),
        }
    )
    write_json(tasks_index_path, tasks_index)
    return remediation_path


def evaluate_artifact(spec: dict[str, Any], artifact: dict[str, Any], retry_count: int = 0) -> dict[str, Any]:
    stage = normalized_stage(str(artifact.get("stage", "")))
    failures: list[str] = []
    hard_fails: list[str] = []

    if stage not in spec.get("stages", STAGE_ORDER):
        failures.append("missing_schema_or_artifact")

    coverage = requirement_mapping_coverage(artifact)
    if coverage < 1.0:
        hard_fails.append("missing_requirement_mapping")
        failures.append(f"coverage:{coverage:.2f}")

    known_evidence = evidence_ids(artifact)
    missing_decision_evidence = core_decision_failures(artifact, known_evidence)
    if missing_decision_evidence:
        hard_fails.append("evidence_free_core_decision")
        failures.append("missing_evidence:core_decisions")

    if required_approval_missing(artifact):
        hard_fails.append("missing_required_user_approval")
        failures.append("missing_required_user_approval")

    if tests_failed(artifact):
        hard_fails.append("test_failure")
        failures.append("test_failure")

    score = float(artifact.get("score", 0.0) or 0.0)
    threshold = stage_threshold(spec, stage)
    if score < threshold:
        failures.append(f"score:{score:.2f}<threshold:{threshold:.2f}")

    issue_counts = count_issues(artifact)
    allowance = issue_allowance(spec, stage)
    for severity in ("critical", "high", "medium"):
        if issue_counts.get(severity, 0) > allowance.get(severity, 0):
            failures.append(f"issue_allowance:{severity}")

    if issue_counts.get("medium", 0) > 0 and not artifact.get("residualRisks"):
        failures.append("missing_residual_risk")

    causes = infer_failure_causes(stage, failures + hard_fails)
    passed = not failures and not hard_fails
    result = {
        "stage": stage,
        "passed": passed,
        "evaluatedAt": now_iso(),
        "score": score,
        "threshold": threshold,
        "requirementMappingCoverage": coverage,
        "issueCounts": issue_counts,
        "issueAllowance": allowance,
        "hardFails": sorted(set(hard_fails)),
        "failureCauses": causes,
        "rollbackTarget": "none" if passed else rollback_target(spec, causes, retry_count),
        "remediationPlan": {
            "retryCount": retry_count,
            "retryLimit": int(spec.get("retryLimit", 2)),
            "steps": [] if passed else remediation_steps(causes),
        },
    }
    return result


def command_init(args: argparse.Namespace) -> int:
    state_dir = state_dir_from(Path(args.root).resolve())
    ensure_stage_gate_files(state_dir)
    print(f"Stage gate files ready: {stage_gate_dir(state_dir)}")
    return 0


def command_evaluate(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    state_dir = state_dir_from(root)
    spec = load_spec(state_dir)
    artifact = load_json(Path(args.artifact).resolve())
    if args.stage:
        artifact = deepcopy(artifact)
        artifact["stage"] = normalized_stage(args.stage)
    result = evaluate_artifact(spec, artifact, retry_count=args.retry_count)
    output_path = Path(args.output).resolve() if args.output else stage_gate_dir(state_dir) / "results" / f"{result['stage']}-latest.json"
    write_json(output_path, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


def command_checkpoint(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    state_dir = state_dir_from(root)
    project_root = project_root_from_state(state_dir)
    spec = load_spec(state_dir)
    stage = normalized_stage(args.stage)
    artifact_path = Path(args.artifact_output).resolve() if args.artifact_output else None
    output_path = Path(args.output).resolve() if args.output else None
    artifact, result, _, _ = checkpoint_stage(
        spec,
        state_dir,
        project_root,
        stage,
        requirements=args.requirement,
        retry_count=args.retry_count,
        artifact_output=artifact_path,
        result_output=output_path,
    )
    if not result.get("passed"):
        next_action = next_action_for_result(spec, result)
        result["remediationTaskPath"] = str(write_remediation_task(state_dir, result, next_action))
    print(json.dumps({"artifact": artifact, "result": result}, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


def command_orchestrate(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    state_dir = state_dir_from(root)
    project_root = project_root_from_state(state_dir)
    spec = load_spec(state_dir)
    try:
        stages = stage_slice(spec, start=args.start, end=args.end, only=args.stage)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    checkpoints: list[dict[str, Any]] = []
    stopped_at = ""
    next_action = {"type": "complete", "reason": "all_requested_stages_passed"}
    for stage in stages:
        retry_count = args.retry_count if args.retry_count >= 0 else previous_retry_count(state_dir, stage)
        _, result, artifact_path, result_path = checkpoint_stage(
            spec,
            state_dir,
            project_root,
            stage,
            requirements=args.requirement,
            retry_count=retry_count,
        )
        checkpoint = {
            "stage": stage,
            "passed": result.get("passed"),
            "score": result.get("score"),
            "threshold": result.get("threshold"),
            "retryCount": result.get("remediationPlan", {}).get("retryCount", retry_count),
            "rollbackTarget": result.get("rollbackTarget"),
            "artifactPath": str(artifact_path),
            "resultPath": str(result_path),
            "hardFails": result.get("hardFails", []),
            "failureCauses": result.get("failureCauses", []),
        }
        checkpoints.append(checkpoint)
        if not result.get("passed"):
            stopped_at = stage
            next_action = next_action_for_result(spec, result)
            remediation_path = write_remediation_task(state_dir, result, next_action)
            next_action["remediationTaskPath"] = str(remediation_path)
            break

    orchestration = {
        "generatedAt": now_iso(),
        "requestedStages": stages,
        "completedStages": [item["stage"] for item in checkpoints if item.get("passed")],
        "stoppedAt": stopped_at,
        "passed": not stopped_at and len(checkpoints) == len(stages),
        "nextAction": next_action,
        "checkpoints": checkpoints,
    }
    output_path = Path(args.output).resolve() if args.output else stage_gate_dir(state_dir) / "orchestration" / "latest.json"
    write_json(output_path, orchestration)
    print(json.dumps(orchestration, ensure_ascii=False, indent=2))
    return 0 if orchestration["passed"] else 1


def command_status(args: argparse.Namespace) -> int:
    state_dir = state_dir_from(Path(args.root).resolve())
    ensure_stage_gate_files(state_dir)
    results_dir = stage_gate_dir(state_dir) / "results"
    latest: dict[str, Any] = {}
    for path in sorted(results_dir.glob("*-latest.json")):
        payload = load_json(path)
        latest[str(payload.get("stage", path.stem))] = {
            "passed": payload.get("passed"),
            "score": payload.get("score"),
            "rollbackTarget": payload.get("rollbackTarget"),
            "evaluatedAt": payload.get("evaluatedAt"),
        }
    print(json.dumps({"stageGateDir": str(stage_gate_dir(state_dir)), "latest": latest}, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate SummitHarness all-rounder Ralph stage-gate artifacts.")
    parser.add_argument("--root", default=".", help="Project root or .codex-loop directory")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Create stage gate spec/results directories")
    init_parser.set_defaults(func=command_init)

    eval_parser = subparsers.add_parser("evaluate", help="Evaluate a stage artifact JSON file")
    eval_parser.add_argument("--stage", default="", help="Override artifact stage")
    eval_parser.add_argument("--artifact", required=True, help="Path to the stage artifact JSON")
    eval_parser.add_argument("--retry-count", type=int, default=0, help="Number of failed attempts already used for this stage")
    eval_parser.add_argument("--output", default="", help="Where to write the gate result JSON")
    eval_parser.set_defaults(func=command_evaluate)

    checkpoint_parser = subparsers.add_parser("checkpoint", help="Generate a stage artifact from local SummitHarness files and evaluate it")
    checkpoint_parser.add_argument("--stage", required=True, help="Stage to checkpoint")
    checkpoint_parser.add_argument("--requirement", action="append", default=[], help="Requirement text to map; can be repeated")
    checkpoint_parser.add_argument("--retry-count", type=int, default=0, help="Number of failed attempts already used for this stage")
    checkpoint_parser.add_argument("--artifact-output", default="", help="Where to write the generated artifact JSON")
    checkpoint_parser.add_argument("--output", default="", help="Where to write the gate result JSON")
    checkpoint_parser.set_defaults(func=command_checkpoint)

    orchestrate_parser = subparsers.add_parser("orchestrate", help="Checkpoint stage gates in order and stop at the first failed gate")
    orchestrate_parser.add_argument("--start", default="", help="First stage to checkpoint")
    orchestrate_parser.add_argument("--end", default="", help="Last stage to checkpoint")
    orchestrate_parser.add_argument("--stage", action="append", default=[], help="Specific stage to checkpoint; can be repeated")
    orchestrate_parser.add_argument("--requirement", action="append", default=[], help="Requirement text to map; can be repeated")
    orchestrate_parser.add_argument(
        "--retry-count",
        type=int,
        default=-1,
        help="Override retry count for every stage. Default reads the previous failed result and increments it.",
    )
    orchestrate_parser.add_argument("--output", default="", help="Where to write the orchestration summary JSON")
    orchestrate_parser.set_defaults(func=command_orchestrate)

    status_parser = subparsers.add_parser("status", help="Summarize latest gate results")
    status_parser.set_defaults(func=command_status)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
