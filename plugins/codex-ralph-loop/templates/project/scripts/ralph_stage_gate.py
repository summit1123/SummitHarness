#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STAGE_ORDER = ["onboarding", "interview", "seed-prd", "research", "design", "r-and-d", "dev", "eval"]
DEFAULT_SPEC: dict[str, Any] = {
    "version": 1,
    "decisionMode": "automatic",
    "retryLimit": 2,
    "stages": STAGE_ORDER,
    "thresholds": {
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


def stage_gate_dir(state_dir: Path) -> Path:
    return state_dir / "stage-gates"


def spec_path(state_dir: Path) -> Path:
    return stage_gate_dir(state_dir) / "spec.json"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_stage_gate_files(state_dir: Path) -> None:
    gates_dir = stage_gate_dir(state_dir)
    (gates_dir / "artifacts").mkdir(parents=True, exist_ok=True)
    (gates_dir / "results").mkdir(parents=True, exist_ok=True)
    if not spec_path(state_dir).exists():
        write_json(spec_path(state_dir), DEFAULT_SPEC)


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

    status_parser = subparsers.add_parser("status", help="Summarize latest gate results")
    status_parser.set_defaults(func=command_status)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
