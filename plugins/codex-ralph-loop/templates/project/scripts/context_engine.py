#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


PRIORITY_ORDER = {"p0": 0, "p1": 1, "p2": 2, "p3": 3}
DEFAULT_DURABLE = {
    "facts": [],
    "constraints": [],
    "style": [],
    "contracts": [],
    "updatedAt": None,
}
DEFAULT_OPEN_QUESTIONS = {"questions": [], "updatedAt": None}
DEFAULT_ASSET_REGISTRY = {"assets": [], "updatedAt": None}
DONE_STATUSES = {"done", "completed", "complete", "skipped"}
NEXT_TASK_STATUSES = {"todo", "pending", "open"}
DEFAULT_TEMPLATE_TASK_TITLES = {
    "Brainstorm and lock the build brief",
    "Write the first execution plan",
    "Build and verify the first vertical slice",
}


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def strip_leading_heading(text: str) -> str:
    stripped = (text or "").strip()
    if not stripped:
        return ""

    lines = stripped.splitlines()
    if lines and lines[0].lstrip().startswith("#"):
        lines = lines[1:]
        while lines and not lines[0].strip():
            lines = lines[1:]
    return "\n".join(lines).strip()


def load_json(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return default.copy()
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    write_text(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def project_root_from(path: Path | None = None) -> Path:
    if path is not None:
        return path.resolve()
    return Path(__file__).resolve().parents[1]


def state_dir_from(root: Path) -> Path:
    return root / ".codex-loop"


def context_dir_from(state_dir: Path) -> Path:
    return state_dir / "context"


def ensure_context_layout(project_root: Path, state_dir: Path) -> None:
    context_dir = context_dir_from(state_dir)
    for rel in ["context", "preflight", "assets", "logs", "history", "reviews", "evals"]:
        (state_dir / rel).mkdir(parents=True, exist_ok=True)

    durable_path = context_dir / "durable.json"
    if not durable_path.exists():
        payload = DEFAULT_DURABLE.copy()
        payload["updatedAt"] = now_iso()
        write_json(durable_path, payload)

    questions_path = context_dir / "open-questions.json"
    if not questions_path.exists():
        payload = DEFAULT_OPEN_QUESTIONS.copy()
        payload["updatedAt"] = now_iso()
        write_json(questions_path, payload)

    registry_path = state_dir / "assets" / "registry.json"
    if not registry_path.exists():
        payload = DEFAULT_ASSET_REGISTRY.copy()
        payload["updatedAt"] = now_iso()
        write_json(registry_path, payload)


def load_tasks_index(state_dir: Path) -> dict[str, Any]:
    tasks_path = state_dir / "tasks.json"
    if not tasks_path.exists():
        return {}
    payload = json.loads(tasks_path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def load_tasks(state_dir: Path) -> list[dict[str, Any]]:
    payload = load_tasks_index(state_dir)
    tasks = payload.get("tasks", [])
    return tasks if isinstance(tasks, list) else []


def tasks_need_seed(tasks_index: dict[str, Any], tasks: list[dict[str, Any]]) -> bool:
    if not tasks:
        return True

    if str(tasks_index.get("source", "")).strip().lower() == "bootstrap-template":
        return True

    project = str(tasks_index.get("project", "")).strip()
    titles = {str(task.get("title", "")).strip() for task in tasks if str(task.get("title", "")).strip()}
    return project == "Codex Ralph Loop Workspace" and titles == DEFAULT_TEMPLATE_TASK_TITLES


def task_file_path(state_dir: Path, task: dict[str, Any]) -> Path:
    rel = task.get("file")
    if rel:
        return state_dir / rel
    return state_dir / "tasks" / f"TASK-{task.get('id', 'UNKNOWN')}.json"


def load_task_specs(state_dir: Path, tasks: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    specs: dict[str, dict[str, Any]] = {}
    for task in tasks:
        path = task_file_path(state_dir, task)
        if path.exists():
            try:
                specs[str(task.get("id"))] = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                specs[str(task.get("id"))] = {}
        else:
            specs[str(task.get("id"))] = {}
    return specs


def task_sort_key(task: dict[str, Any]) -> tuple[int, str]:
    priority = PRIORITY_ORDER.get(str(task.get("priority", "p2")).lower(), 9)
    return priority, str(task.get("id", "ZZZ"))


def task_status_line(task: dict[str, Any], spec: dict[str, Any]) -> str:
    deps = spec.get("dependsOn", []) if isinstance(spec, dict) else []
    dep_text = f" deps={','.join(str(item) for item in deps)}" if deps else ""
    return f"- [{task.get('status', 'todo')}] {task.get('id')} {task.get('title', '')}{dep_text}".rstrip()


def recent_log_blocks(log_path: Path, limit: int = 3) -> list[str]:
    if not log_path.exists():
        return []
    text = log_path.read_text(encoding="utf-8").strip()
    if not text or "## Iteration " not in text:
        return []
    blocks = []
    for chunk in text.split("## Iteration ")[1:]:
        chunk = chunk.strip()
        if not chunk:
            continue
        blocks.append("## Iteration " + chunk)
    return blocks[-limit:]


def is_promise_only_text(text: str) -> bool:
    stripped = (text or "").strip()
    if not stripped:
        return False
    return bool(__import__("re").fullmatch(r"(?:<promise>.*?</promise>\s*)+", stripped, __import__("re").DOTALL))


def first_bullet(lines: list[str]) -> str:
    saw_promise = False
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if is_promise_only_text(stripped.lstrip("- ").strip()):
            saw_promise = True
            continue
        return stripped
    return "Completion promise emitted." if saw_promise else "No summary available."


def summarize_iteration_block(lines: list[str]) -> str:
    for line in lines:
        stripped = line.strip()
        if stripped.lower().startswith("- summary:"):
            summary = stripped.split(":", 1)[1].strip()
            if summary and not is_promise_only_text(summary):
                return summary
            if summary:
                return "Completion promise emitted."

    skip_prefixes = ("- task:", "- promise:", "- checks:", "- review:", "- goal eval:")
    for line in lines:
        stripped = line.strip()
        candidate = stripped.lstrip("- ").strip()
        if stripped and not stripped.lower().startswith(skip_prefixes) and not is_promise_only_text(candidate):
            return candidate

    return first_bullet(lines)


def summarize_recent_progress(state_dir: Path) -> list[str]:
    blocks = recent_log_blocks(state_dir / "logs" / "LOG.md")
    result: list[str] = []
    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        header = lines[0].replace("## ", "") if lines else "Iteration"
        summary = summarize_iteration_block(lines[1:])
        result.append(f"- {header}: {summary}")
    return result


def summarize_assets(state_dir: Path) -> list[str]:
    registry = load_json(state_dir / "assets" / "registry.json", DEFAULT_ASSET_REGISTRY)
    assets = registry.get("assets", [])
    if not isinstance(assets, list):
        return []
    approved = [asset for asset in assets if str(asset.get("status", "")).lower() in {"approved", "reference", "selected"}]
    lines = []
    for asset in approved[:5]:
        title = asset.get("title") or asset.get("path") or "asset"
        kind = asset.get("kind", "unknown")
        source = asset.get("source", "unknown")
        lines.append(f"- {title} ({kind}, source={source})")
    return lines


def latest_pdf_review(state_dir: Path) -> dict[str, Any]:
    review_dir = state_dir / "artifacts" / "pdf-review"
    if not review_dir.exists():
        return {}
    candidates = sorted(review_dir.glob("*-review.json"), key=lambda item: item.stat().st_mtime, reverse=True)
    for path in candidates:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            payload["_reviewPath"] = str(path)
            return payload
    return {}


def summarize_pdf_review(state_dir: Path) -> tuple[list[str], list[str]]:
    payload = latest_pdf_review(state_dir)
    if not payload:
        return [], []

    info = payload.get("file", {}) if isinstance(payload.get("file"), dict) else {}
    metadata = payload.get("metadata", {}) if isinstance(payload.get("metadata"), dict) else {}
    blockers = payload.get("blockers", [])
    warnings = payload.get("warnings", [])
    lines = [
        f"- Latest review: {info.get('name', 'unknown')} ({info.get('sizeMegabytes', 'n/a')} MB, {metadata.get('pages', 'unknown')} pages)",
        f"- Submission blockers: {len(blockers) if isinstance(blockers, list) else 0}",
        f"- Submission warnings: {len(warnings) if isinstance(warnings, list) else 0}",
    ]
    if isinstance(blockers, list) and blockers:
        lines.append(f"- Top blocker: {blockers[0]}")
    elif isinstance(warnings, list) and warnings:
        lines.append(f"- Top warning: {warnings[0]}")
    return lines, blockers if isinstance(blockers, list) else []


def summarize_preflight(state_dir: Path) -> tuple[list[str], list[str]]:
    status = load_json(state_dir / "preflight" / "status.json", {})
    blockers = status.get("blockers", []) if isinstance(status, dict) else []
    warnings = status.get("warnings", []) if isinstance(status, dict) else []
    return [f"- {item}" for item in blockers[:5]], [f"- {item}" for item in warnings[:5]]


def summarize_durable(state_dir: Path) -> dict[str, list[str]]:
    durable = load_json(context_dir_from(state_dir) / "durable.json", DEFAULT_DURABLE)
    result: dict[str, list[str]] = {}
    for key in ["facts", "constraints", "style", "contracts"]:
        values = durable.get(key, [])
        if isinstance(values, list):
            result[key] = [f"- {str(item)}" for item in values[:6]]
        else:
            result[key] = []
    return result


def summarize_open_questions(state_dir: Path) -> list[str]:
    payload = load_json(context_dir_from(state_dir) / "open-questions.json", DEFAULT_OPEN_QUESTIONS)
    questions = payload.get("questions", [])
    if not isinstance(questions, list):
        return []
    lines = []
    for item in questions[:5]:
        text = item.get("text", "") if isinstance(item, dict) else str(item)
        if text:
            lines.append(f"- {text}")
    return lines


def next_best_step(
    tasks_index: dict[str, Any],
    tasks: list[dict[str, Any]],
    specs: dict[str, dict[str, Any]],
    blockers: list[str],
    submission_blockers: list[str] | None = None,
) -> str:
    if blockers:
        return "Resolve the preflight blockers before the next autonomous run."
    if submission_blockers:
        return "Resolve the submission PDF blockers and regenerate the attachment before declaring the goal complete."
    if tasks_need_seed(tasks_index, tasks):
        return "Tighten the PRD and local checks, then let the first Ralph run auto-generate the real task graph."
    for task in sorted(tasks, key=task_sort_key):
        if str(task.get("status", "")).lower() == "in_progress":
            return f"Continue task {task.get('id')} and keep task state accurate."
    for task in sorted(tasks, key=task_sort_key):
        if str(task.get("status", "")).lower() in NEXT_TASK_STATUSES:
            deps = specs.get(str(task.get("id")), {}).get("dependsOn", [])
            if deps:
                return f"Check whether task {task.get('id')} is now unblocked by {', '.join(str(dep) for dep in deps)}."
            return f"Start the highest-priority runnable task: {task.get('id')} {task.get('title', '')}.".strip()
    return "Run local checks, inspect the latest output, and tighten the acceptance bar."


def build_context_markdown(project_root: Path, state_dir: Path) -> tuple[str, str, dict[str, Any]]:
    ensure_context_layout(project_root, state_dir)
    summary = strip_leading_heading(read_text(state_dir / "prd" / "SUMMARY.md")) or "No project summary yet."
    prompt = read_text(state_dir / "PROMPT.md")
    tasks_index = load_tasks_index(state_dir)
    tasks = load_tasks(state_dir)
    specs = load_task_specs(state_dir, tasks)
    seed_pending = tasks_need_seed(tasks_index, tasks)
    open_tasks = [task for task in sorted(tasks, key=task_sort_key) if str(task.get("status", "")).lower() not in DONE_STATUSES]
    active_task = None if seed_pending else next((task for task in open_tasks if str(task.get("status", "")).lower() == "in_progress"), None)
    latest_state = load_json(state_dir / "state.json", {})
    latest_hook = load_json(state_dir / "ralph-loop.json", {})
    blockers, warnings = summarize_preflight(state_dir)
    durable = summarize_durable(state_dir)
    questions = summarize_open_questions(state_dir)
    assets = summarize_assets(state_dir)
    pdf_review_lines, pdf_blockers = summarize_pdf_review(state_dir)
    recent = summarize_recent_progress(state_dir)

    if seed_pending:
        open_task_lines = ["- Bootstrap template is still active. The first Ralph run will replace it with a project-specific task graph."]
    else:
        open_task_lines = [task_status_line(task, specs.get(str(task.get("id")), {})) for task in open_tasks[:6]]
    active_task_line = (
        f"- {active_task.get('id')} {active_task.get('title')} ({active_task.get('status')})"
        if active_task
        else "- No task is currently marked in_progress."
    )

    current_state_lines = [
        "# Working Context",
        "",
        "## Project Summary",
        summary,
        "",
        "## Current Execution State",
        active_task_line,
        f"- Loop iteration: {latest_state.get('iteration', 'n/a')} / {latest_state.get('maxIterations', 'n/a')}",
        f"- Checks: {latest_state.get('checksSummary', 'No loop checks have run yet.')}",
        f"- Review: {latest_state.get('reviewSummary', 'No review gate has run yet.')}",
        f"- Goal eval: {latest_state.get('evalSummary', 'No goal evaluator result yet.')}",
        f"- Hook loop: {latest_hook.get('status', 'inactive')}",
        "",
        "## Open Tasks",
        *(open_task_lines or ["- No open tasks remain."]),
        "",
        "## Durable Facts",
        *(durable["facts"] or ["- None yet."]),
        "",
        "## Durable Constraints",
        *(durable["constraints"] or ["- None yet."]),
        "",
        "## Design Direction",
        *(durable["style"] or ["- No approved visual direction has been captured yet."]),
        "",
        "## Contracts",
        *(durable["contracts"] or ["- No durable contracts captured yet."]),
        "",
        "## Approved Assets",
        *(assets or ["- No approved assets registered yet."]),
        "",
        "## Submission PDF Gate",
        *(pdf_review_lines or ["- No submission PDF review captured yet."]),
        "",
        "## Recent Progress",
        *(recent or ["- No recent loop log entries yet."]),
        "",
        "## Preflight Blockers",
        *(blockers or ["- None detected."]),
        "",
        "## Preflight Warnings",
        *(warnings or ["- None detected."]),
        "",
        "## Open Questions",
        *(questions or ["- None captured."]),
        "",
        "## Stable Prompt Reminder",
        prompt or "No stable prompt has been written yet.",
        "",
    ]

    next_step = next_best_step(tasks_index, tasks, specs, blockers, pdf_blockers)
    handoff_lines = [
        "# Compressed Handoff",
        "",
        f"- Repo: {project_root}",
        f"- Next best step: {next_step}",
        f"- Active task: {active_task.get('id')} {active_task.get('title')}" if active_task else "- Active task: none",
        f"- Check state: {latest_state.get('checksSummary', 'not run')}",
        f"- Review state: {latest_state.get('reviewSummary', 'not run')}",
        f"- Goal eval: {latest_state.get('evalSummary', 'not run')}",
        f"- Hook state: {latest_hook.get('status', 'inactive')}",
        "",
        "## Must Remember",
        *(durable["constraints"][:4] or ["- Keep the PRD, tasks, and real repo state aligned."]),
        "",
        "## Visual Direction",
        *(durable["style"][:4] or ["- No approved visual system yet. Generate or import one before polishing code-only UI."]),
        "",
        "## Submission Gate",
        *(pdf_review_lines[:4] or ["- No submission PDF review captured yet."]),
        "",
        "## Open Tasks",
        *(open_task_lines[:4] or ["- No open tasks remain."]),
        "",
        "## Recent Progress",
        *(recent[:3] or ["- No recent progress logged yet."]),
        "",
        "## Open Questions",
        *(questions[:3] or ["- None."]),
        "",
    ]

    payload = {
        "updatedAt": now_iso(),
        "projectRoot": str(project_root),
        "activeTask": active_task,
        "openTaskCount": 0 if seed_pending else len(open_tasks),
        "nextBestStep": next_step,
        "preflightBlockers": blockers,
        "preflightWarnings": warnings,
        "approvedAssets": assets,
        "submissionPdf": pdf_review_lines,
        "evalSummary": latest_state.get("evalSummary", "not run"),
    }
    return "\n".join(current_state_lines).rstrip() + "\n", "\n".join(handoff_lines).rstrip() + "\n", payload


def refresh_context(project_root: Path, state_dir: Path, source: str = "manual") -> dict[str, Any]:
    working, handoff, payload = build_context_markdown(project_root, state_dir)
    context_dir = context_dir_from(state_dir)
    write_text(context_dir / "current-state.md", working)
    write_text(context_dir / "handoff.md", handoff)
    append_jsonl(
        context_dir / "events.jsonl",
        {
            "timestamp": payload["updatedAt"],
            "source": source,
            "nextBestStep": payload["nextBestStep"],
            "openTaskCount": payload["openTaskCount"],
            "activeTaskId": payload["activeTask"].get("id") if isinstance(payload.get("activeTask"), dict) else None,
        },
    )
    return payload


def remember_item(project_root: Path, state_dir: Path, kind: str, text: str) -> None:
    ensure_context_layout(project_root, state_dir)
    timestamp = now_iso()
    if kind == "question":
        path = context_dir_from(state_dir) / "open-questions.json"
        payload = load_json(path, DEFAULT_OPEN_QUESTIONS)
        questions = payload.setdefault("questions", [])
        questions.append({"text": text, "createdAt": timestamp})
        payload["updatedAt"] = timestamp
        write_json(path, payload)
        return

    path = context_dir_from(state_dir) / "durable.json"
    payload = load_json(path, DEFAULT_DURABLE)
    bucket = payload.setdefault(kind, [])
    bucket.append(text)
    payload["updatedAt"] = timestamp
    write_json(path, payload)


def load_status(project_root: Path, state_dir: Path) -> dict[str, Any]:
    ensure_context_layout(project_root, state_dir)
    _, handoff, payload = build_context_markdown(project_root, state_dir)
    payload["handoff"] = handoff
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compressed context engine for SummitHarness.")
    parser.add_argument("--root", help="Project root. Defaults to the repository that owns this script.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_cmd = subparsers.add_parser("init", help="Create the context engine files if missing")
    init_cmd.set_defaults(command_name="init")

    refresh_cmd = subparsers.add_parser("refresh", help="Refresh working memory and handoff from repo state")
    refresh_cmd.add_argument("--source", default="manual", help="Event source label for the refresh record")
    refresh_cmd.set_defaults(command_name="refresh")

    remember_cmd = subparsers.add_parser("remember", help="Store a durable fact, constraint, style rule, contract, or question")
    remember_cmd.add_argument("--kind", choices=["facts", "constraints", "style", "contracts", "question"], required=True)
    remember_cmd.add_argument("--text", required=True)
    remember_cmd.set_defaults(command_name="remember")

    status_cmd = subparsers.add_parser("status", help="Show the current compressed context packet")
    status_cmd.add_argument("--json", action="store_true")
    status_cmd.set_defaults(command_name="status")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    project_root = project_root_from(Path(args.root).expanduser() if args.root else None)
    state_dir = state_dir_from(project_root)

    if args.command == "init":
        ensure_context_layout(project_root, state_dir)
        refresh_context(project_root, state_dir, source="init")
        print(f"Initialized context engine in {state_dir / 'context'}")
        return 0

    if args.command == "refresh":
        payload = refresh_context(project_root, state_dir, source=args.source)
        print(f"Refreshed context packet: {state_dir / 'context' / 'handoff.md'}")
        print(f"Next best step: {payload['nextBestStep']}")
        return 0

    if args.command == "remember":
        remember_item(project_root, state_dir, args.kind, args.text.strip())
        payload = refresh_context(project_root, state_dir, source=f"remember:{args.kind}")
        print(f"Stored {args.kind} and refreshed context.")
        print(f"Next best step: {payload['nextBestStep']}")
        return 0

    payload = load_status(project_root, state_dir)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(payload["handoff"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
