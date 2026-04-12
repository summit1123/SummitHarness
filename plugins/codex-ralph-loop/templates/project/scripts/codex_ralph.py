#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import shlex
import subprocess
import sys
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from context_engine import ensure_context_layout, refresh_context


COMPLETE_EXIT = 0
MAX_ITER_EXIT = 1
BLOCKED_EXIT = 2
DECIDE_EXIT = 3
ERROR_EXIT = 4

PROMISE_RE = re.compile(r"<promise>(.*?)</promise>", re.DOTALL)
REVIEW_RE = re.compile(r"RESULT:\s*(PASS|FAIL)", re.IGNORECASE)
EVAL_RESULT_RE = re.compile(r"RESULT:\s*(PASS|FAIL)", re.IGNORECASE)
EVAL_STATUS_RE = re.compile(r"STATUS:\s*(COMPLETE|INCOMPLETE|BLOCKED|DECIDE)", re.IGNORECASE)
PRIORITY_ORDER = {"p0": 0, "p1": 1, "p2": 2, "p3": 3}
OPEN_TASK_STATUSES = {"todo", "in_progress", "pending", "open"}
NEXT_TASK_STATUSES = {"todo", "pending", "open"}
DEFAULT_TEMPLATE_TASK_TITLES = {
    "Brainstorm and lock the build brief",
    "Write the first execution plan",
    "Build and verify the first vertical slice",
}

DEFAULT_CONFIG: dict[str, Any] = {
    "version": 1,
    "agent": {
        "command": [
            "codex",
            "exec",
            "--full-auto",
            "--skip-git-repo-check",
            "--cd",
            "{project_root}",
            "--output-last-message",
            "{output_last_message}",
            "-",
        ],
        "review_command": [
            "codex",
            "exec",
            "-s",
            "read-only",
            "--skip-git-repo-check",
            "--cd",
            "{project_root}",
            "--output-last-message",
            "{output_last_message}",
            "-",
        ],
        "env": {},
    },
    "loop": {
        "completion_promise": "COMPLETE",
        "max_iterations": 8,
        "mode": "implementation",
        "auto_seed_tasks": True,
    },
    "checks": {
        "commands": [],
        "stop_on_failure": True,
    },
    "review": {
        "enabled": True,
        "max_findings": 5,
    },
    "evaluator": {
        "enabled": True,
        "require_pass_for_completion": True,
        "auto_extend_tasks": True,
    },
    "context": {
        "enabled": True,
        "refresh_each_iteration": True,
    },
}


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    write_text(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def in_git_repo(project_root: Path) -> bool:
    result = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=project_root,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0 and result.stdout.strip() == "true"


def resolve_check_shell() -> list[str]:
    candidates: list[tuple[str, str]] = []
    shell_env = os.environ.get("SHELL")
    if shell_env:
        flag = "-c" if Path(shell_env).name == "sh" else "-lc"
        candidates.append((shell_env, flag))
    candidates.extend(
        [
            ("/bin/zsh", "-lc"),
            ("/bin/bash", "-lc"),
            ("/usr/bin/bash", "-lc"),
            ("/bin/sh", "-c"),
            ("sh", "-c"),
        ]
    )

    seen: set[str] = set()
    for shell_path, flag in candidates:
        if shell_path in seen:
            continue
        seen.add(shell_path)
        resolved = shell_path
        if os.path.isabs(shell_path):
            if not os.path.exists(shell_path):
                continue
        else:
            found = shutil.which(shell_path)
            if not found:
                continue
            resolved = found
        return [resolved, flag]

    raise FileNotFoundError("No supported shell found for local checks.")


def normalize_command(command_value: Any) -> list[str]:
    if isinstance(command_value, str):
        return shlex.split(command_value)
    if isinstance(command_value, list):
        return [str(part) for part in command_value]
    raise TypeError(f"unsupported command: {command_value!r}")


def render_command(command_value: Any, context: dict[str, str]) -> list[str]:
    template = normalize_command(command_value)
    return [part.format(**context) for part in template]


def load_config(project_root: Path, state_dir: Path, args: argparse.Namespace) -> dict[str, Any]:
    config_path = state_dir / "config.json"
    user_config = load_json(config_path) if config_path.exists() else {}
    config = deep_merge(DEFAULT_CONFIG, user_config)

    if args.mode:
        config["loop"]["mode"] = args.mode
    if args.max_iterations is not None:
        config["loop"]["max_iterations"] = args.max_iterations
    if args.once:
        config["loop"]["max_iterations"] = 1

    agent_override = args.agent_cmd or os.environ.get("CODEX_RALPH_AGENT_CMD")
    if agent_override:
        config["agent"]["command"] = shlex.split(agent_override)

    review_override = args.review_cmd or os.environ.get("CODEX_RALPH_REVIEW_CMD")
    if review_override:
        config["agent"]["review_command"] = shlex.split(review_override)

    return config


def load_tasks_index(state_dir: Path) -> dict[str, Any]:
    return load_json(state_dir / "tasks.json")


def load_tasks(state_dir: Path) -> list[dict[str, Any]]:
    tasks_index = load_tasks_index(state_dir)
    tasks = tasks_index.get("tasks", [])
    if not isinstance(tasks, list):
        raise ValueError(".codex-loop/tasks.json must contain a 'tasks' array")
    return tasks


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
            specs[str(task.get("id"))] = load_json(path)
        else:
            specs[str(task.get("id"))] = {}
    return specs


def task_sort_key(task: dict[str, Any]) -> tuple[int, str]:
    priority = PRIORITY_ORDER.get(str(task.get("priority", "p2")).lower(), 9)
    return priority, str(task.get("id", "ZZZ"))


def task_is_done(task: dict[str, Any]) -> bool:
    return str(task.get("status", "")).lower() in {"done", "completed", "complete", "skipped"}


def task_dependencies(task: dict[str, Any], specs: dict[str, dict[str, Any]]) -> list[str]:
    spec = specs.get(str(task.get("id")), {})
    deps = spec.get("dependsOn", task.get("dependsOn", []))
    if not isinstance(deps, list):
        return []
    return [str(dep) for dep in deps]


def task_is_ready(task: dict[str, Any], specs: dict[str, dict[str, Any]], done_ids: set[str]) -> bool:
    return all(dep in done_ids for dep in task_dependencies(task, specs))


def select_task(tasks: list[dict[str, Any]], specs: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    done_ids = {str(task.get("id")) for task in tasks if task_is_done(task)}
    in_progress = [task for task in tasks if str(task.get("status", "")).lower() == "in_progress"]
    ready_in_progress = [task for task in in_progress if task_is_ready(task, specs, done_ids)]
    if ready_in_progress:
        return sorted(ready_in_progress, key=task_sort_key)[0]

    todo = [task for task in tasks if str(task.get("status", "")).lower() in NEXT_TASK_STATUSES]
    ready_todo = [task for task in todo if task_is_ready(task, specs, done_ids)]
    if ready_todo:
        return sorted(ready_todo, key=task_sort_key)[0]
    return None


def blocked_tasks(tasks: list[dict[str, Any]], specs: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    done_ids = {str(task.get("id")) for task in tasks if task_is_done(task)}
    pending = [task for task in tasks if str(task.get("status", "")).lower() in OPEN_TASK_STATUSES]
    return [task for task in pending if not task_is_ready(task, specs, done_ids)]


def tasks_need_seed(tasks_index: dict[str, Any], tasks: list[dict[str, Any]]) -> bool:
    if not tasks:
        return True

    source = str(tasks_index.get("source", "")).strip().lower()
    if source == "bootstrap-template":
        return True

    project = str(tasks_index.get("project", "")).strip()
    titles = {str(task.get("title", "")).strip() for task in tasks if str(task.get("title", "")).strip()}
    if project == "Codex Ralph Loop Workspace" and titles == DEFAULT_TEMPLATE_TASK_TITLES:
        return True

    return False


def all_tasks_complete(tasks: list[dict[str, Any]]) -> bool:
    return bool(tasks) and all(task_is_done(task) for task in tasks)


def current_active_task(tasks: list[dict[str, Any]], specs: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    in_progress = [task for task in tasks if str(task.get("status", "")).lower() == "in_progress"]
    if not in_progress:
        return None

    done_ids = {str(task.get("id")) for task in tasks if task_is_done(task)}
    ready = [task for task in in_progress if task_is_ready(task, specs, done_ids)]
    if ready:
        return sorted(ready, key=task_sort_key)[0]
    return sorted(in_progress, key=task_sort_key)[0]


def load_current_task_snapshot(state_dir: Path) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], dict[str, Any] | None, dict[str, Any] | None]:
    tasks = load_tasks(state_dir)
    specs = load_task_specs(state_dir, tasks)
    active_task = current_active_task(tasks, specs)
    active_task_body = specs.get(str(active_task.get("id"))) if active_task else None
    return tasks, specs, active_task, active_task_body


def active_steering(steering_text: str) -> str:
    stripped = steering_text.strip()
    if not stripped or "Add urgent notes" in stripped:
        return ""
    return stripped


def parse_promise(text: str) -> str:
    match = PROMISE_RE.search(text or "")
    if not match:
        return ""
    return " ".join(match.group(1).split())


def parse_review_result(text: str) -> tuple[bool, str]:
    match = REVIEW_RE.search(text or "")
    if not match:
        return False, "Reviewer did not emit RESULT: PASS or RESULT: FAIL."
    verdict = match.group(1).upper() == "PASS"
    return verdict, first_nonempty_line(text)


def prefixed_value(text: str, label: str) -> str:
    needle = f"{label.strip().upper()}:"
    for line in (text or "").splitlines():
        stripped = line.strip()
        if stripped.upper().startswith(needle):
            return stripped.split(":", 1)[1].strip()
    return ""


def parse_evaluator_result(text: str) -> dict[str, Any]:
    result_match = EVAL_RESULT_RE.search(text or "")
    status_match = EVAL_STATUS_RE.search(text or "")
    summary = prefixed_value(text, "SUMMARY") or first_nonempty_line(text) or "Evaluator did not provide a summary."
    next_step = prefixed_value(text, "NEXT") or summary

    if not result_match:
        return {
            "passed": False,
            "status": "INCOMPLETE",
            "summary": "Evaluator did not emit RESULT: PASS or RESULT: FAIL.",
            "next": "Inspect the evaluator prompt or eval log.",
            "raw": text,
        }

    passed = result_match.group(1).upper() == "PASS"
    status = status_match.group(1).upper() if status_match else ("COMPLETE" if passed else "INCOMPLETE")
    return {
        "passed": passed,
        "status": status,
        "summary": summary,
        "next": next_step,
        "raw": text,
    }


def should_auto_extend_tasks(tasks: list[dict[str, Any]], evaluation: dict[str, Any], config: dict[str, Any]) -> bool:
    evaluator_cfg = config.get("evaluator", {})
    return (
        bool(evaluator_cfg.get("enabled", True))
        and bool(evaluator_cfg.get("auto_extend_tasks", True))
        and all_tasks_complete(tasks)
        and not bool(evaluation.get("passed"))
        and str(evaluation.get("status", "INCOMPLETE")).upper() == "INCOMPLETE"
    )


def is_promise_only_text(text: str) -> bool:
    stripped = (text or "").strip()
    if not stripped:
        return False
    return bool(re.fullmatch(r"(?:<promise>.*?</promise>\s*)+", stripped, re.DOTALL))


def first_nonempty_line(text: str, limit: int = 160) -> str:
    saw_promise = False
    for line in (text or "").splitlines():
        line = line.strip()
        if not line:
            continue
        if is_promise_only_text(line):
            saw_promise = True
            continue
        return line[:limit]
    return "Completion promise emitted."[:limit] if saw_promise else ""


def build_task_seed_prompt(
    *,
    config: dict[str, Any],
    state_dir: Path,
    steering_text: str,
    git_available: bool,
) -> str:
    prompt_md = read_text(state_dir / "PROMPT.md")
    prd_md = read_text(state_dir / "prd" / "PRD.md")
    summary_md = read_text(state_dir / "prd" / "SUMMARY.md")
    handoff_md = read_text(state_dir / "context" / "handoff.md") or "No compressed handoff exists yet."
    steering_block = steering_text or "No active steering notes."
    git_note = (
        "Git is available. Replace the template task graph with a real one and keep the files synchronized."
        if git_available
        else "Git is not available. Work directly in the workspace and keep the generated task files synchronized."
    )
    scaffold_note = (
        "Bootstrap scaffolding such as `.gitignore`, `ralph.sh`, `.codex/`, `scripts/`, and `.codex-loop/` may already be present. Treat those generated runtime files as expected setup, not unrelated drift."
    )

    return f'''You are initializing the SummitHarness task graph for the first real loop run.

Mode: {config['loop']['mode']}
Promise contract:
- Emit <promise>DECIDE:question</promise> only if a critical ambiguity blocks trustworthy planning.
- Emit <promise>BLOCKED:reason</promise> only if you truly cannot proceed.
- Emit <promise>{config['loop']['completion_promise']}</promise> only when the bootstrap task graph is ready for execution.

Your job right now is planning, not product implementation.

Required outcomes:
- Replace the template `.codex-loop/tasks.json` with a project-specific task graph.
- Replace the placeholder `.codex-loop/tasks/TASK-*.json` files with task specs that match the actual goal.
- Tighten `.codex-loop/prd/PRD.md` and `.codex-loop/prd/SUMMARY.md` if the current brief is too vague.
- Leave the repo with one clearly runnable first task.

Planning rules:
- Prefer 3 to 7 tasks unless the repo state clearly demands otherwise.
- Use a Superpowers-style shape when it fits: brainstorm/spec lock -> execution plan -> implementation slices -> verification.
- The first task should usually lock the brief, users, constraints, and acceptance bar unless that work is already done.
- The second task should usually turn the approved brief into an executable plan or task graph refinement.
- Later tasks should be vertical slices with real dependencies and explicit verification.
- Include acceptance criteria and concrete deliverables in each task file.
- Record assumptions instead of hiding them.
- Do not keep the default sample tasks unless they genuinely match the project.
- Do not implement the product itself in this bootstrap step unless a tiny edit is required to clarify planning state.
- Prefer high-signal files like the PRD, summary, README, docs, and tests before crawling unrelated parts of the repo.
- Stop exploring once you have enough evidence to write a trustworthy first task graph.
- {git_note}
- {scaffold_note}

Compressed context packet:
{handoff_md}

Base prompt:
{prompt_md}

Current PRD:
{prd_md}

Current summary:
{summary_md}

Steering:
{steering_block}
'''


def build_worker_prompt(
    *,
    config: dict[str, Any],
    state_dir: Path,
    iteration: int,
    task: dict[str, Any] | None,
    task_body: dict[str, Any] | None,
    steering_text: str,
    git_available: bool,
) -> str:
    prompt_md = read_text(state_dir / "PROMPT.md")
    summary_md = read_text(state_dir / "prd" / "SUMMARY.md")
    handoff_md = read_text(state_dir / "context" / "handoff.md") or "No compressed handoff exists yet."
    task_index = json.dumps(task, ensure_ascii=False, indent=2) if task else "{}"
    task_spec = json.dumps(task_body or {}, ensure_ascii=False, indent=2)
    steering_block = steering_text or "No active steering notes."
    git_note = (
        "Git is available. Prefer small, reviewable changes and keep task state in sync."
        if git_available
        else "Git is not available. Work directly in the workspace and keep task state files accurate."
    )

    return f"""You are inside a long-running SummitHarness Codex loop.

Iteration: {iteration}
Mode: {config['loop']['mode']}
Promise contract:
- Emit <promise>BLOCKED:reason</promise> only when you truly need human help.
- Emit <promise>DECIDE:question</promise> only when a human decision is unavoidable.
- Emit <promise>{config['loop']['completion_promise']}</promise> only when every open task is genuinely complete.
- Do not lie with promise tags to exit the loop.

Loop expectations:
- Work from the project brief, compressed context packet, and active task below.
- Update .codex-loop/tasks.json and the active task file when task state changes.
- Prefer ending the turn with real progress in files, not just a plan.
- {git_note}
- Keep the visual direction intentional. If the design is still generic, improve the design inputs before polishing implementation details.

Compressed context packet:
{handoff_md}

Base prompt:
{prompt_md}

Project summary:
{summary_md}

Active task index entry:
```json
{task_index}
```

Active task spec:
```json
{task_spec}
```

Steering:
{steering_block}
"""


def build_review_prompt(
    *,
    config: dict[str, Any],
    state_dir: Path,
    task: dict[str, Any] | None,
    task_body: dict[str, Any] | None,
    checks_summary: str,
) -> str:
    summary_md = read_text(state_dir / "prd" / "SUMMARY.md")
    handoff_md = read_text(state_dir / "context" / "handoff.md")
    task_index = json.dumps(task, ensure_ascii=False, indent=2) if task else "{}"
    task_spec = json.dumps(task_body or {}, ensure_ascii=False, indent=2)

    return f"""You are the review gate for a SummitHarness Codex loop. Work read-only.

Review focus:
- correctness bugs
- regressions
- unmet acceptance criteria
- missing tests for changed behavior
- design or UX mismatches only when they materially violate the task

Ignore style-only nits.
Keep the review short and severe-only.
Limit yourself to at most {int(config['review'].get('max_findings', 5))} findings.

Compressed context packet:
{handoff_md or 'No compressed handoff exists yet.'}

Project summary:
{summary_md}

Active task index entry:
```json
{task_index}
```

Active task spec:
```json
{task_spec}
```

Checks summary:
{checks_summary}

Respond exactly in this shape:
RESULT: PASS or FAIL
SUMMARY: one sentence
FINDINGS:
- none

Use FAIL only when there is at least one material issue still open.
"""


def build_goal_eval_prompt(
    *,
    config: dict[str, Any],
    state_dir: Path,
    task: dict[str, Any] | None,
    task_body: dict[str, Any] | None,
    checks_summary: str,
    review_summary: str,
) -> str:
    prd_md = read_text(state_dir / "prd" / "PRD.md")
    summary_md = read_text(state_dir / "prd" / "SUMMARY.md")
    handoff_md = read_text(state_dir / "context" / "handoff.md") or "No compressed handoff exists yet."
    tasks_index = load_tasks_index(state_dir)
    task_graph = json.dumps(tasks_index, ensure_ascii=False, indent=2)
    task_index = json.dumps(task, ensure_ascii=False, indent=2) if task else "{}"
    task_spec = json.dumps(task_body or {}, ensure_ascii=False, indent=2)

    return f"""You are the goal evaluator for a SummitHarness Codex loop. Work read-only.

Judge whether the actual goal has been met, not just whether the listed tasks were checked off.
Focus on:
- goal completion against the PRD and summary
- missing deliverables or weak evidence
- task graph drift, where remaining work is not represented in the plan
- false completion claims

Project summary:
{summary_md}

Current PRD:
{prd_md}

Compressed context packet:
{handoff_md}

Current task graph:
```json
{task_graph}
```

Active task index entry:
```json
{task_index}
```

Active task spec:
```json
{task_spec}
```

Checks summary:
{checks_summary}

Review summary:
{review_summary}

Respond exactly in this shape:
RESULT: PASS or FAIL
STATUS: COMPLETE or INCOMPLETE or BLOCKED or DECIDE
SUMMARY: one sentence
NEXT: one sentence
MISSING:
- none

Rules:
- PASS only when the repo is genuinely in a shippable state for the current goal.
- FAIL if work remains, evidence is weak, or the task graph no longer covers the goal.
- Use BLOCKED only when a real external blocker prevents trustworthy progress.
- Use DECIDE only when a real human product decision is required.
"""


def build_task_replan_prompt(
    *,
    config: dict[str, Any],
    state_dir: Path,
    steering_text: str,
    git_available: bool,
    evaluation: dict[str, Any],
) -> str:
    prompt_md = read_text(state_dir / "PROMPT.md")
    prd_md = read_text(state_dir / "prd" / "PRD.md")
    summary_md = read_text(state_dir / "prd" / "SUMMARY.md")
    handoff_md = read_text(state_dir / "context" / "handoff.md") or "No compressed handoff exists yet."
    tasks_index = load_tasks_index(state_dir)
    task_graph = json.dumps(tasks_index, ensure_ascii=False, indent=2)
    steering_block = steering_text or "No active steering notes."
    git_note = (
        "Git is available. Refresh the task graph in place and keep completed work accurately marked."
        if git_available
        else "Git is not available. Refresh the task graph in place and keep completed work accurately marked."
    )

    return f"""You are refreshing the SummitHarness task graph because the goal evaluator found remaining work.

Mode: {config['loop']['mode']}
Promise contract:
- Emit <promise>DECIDE:question</promise> only if a critical ambiguity blocks trustworthy replanning.
- Emit <promise>BLOCKED:reason</promise> only if you truly cannot proceed.
- Emit <promise>{config['loop']['completion_promise']}</promise> only when the task graph has been updated and there is a clear next action.

Your job right now is planning, not product implementation.

Required outcomes:
- Update `.codex-loop/tasks.json` and `.codex-loop/tasks/TASK-*.json` so the remaining work is represented truthfully.
- Preserve or mark already completed work accurately instead of erasing it.
- Use only `todo`, `in_progress`, or `done`/`completed` style statuses in `tasks.json`; do not invent labels like `pending`.
- Add, reopen, reorder, or tighten tasks so there is one clearly runnable next task.
- If the goal is actually complete and only task state drifted, fix the task state instead of inventing fake work.
- {git_note}

Goal evaluator verdict:
RESULT: {'PASS' if evaluation.get('passed') else 'FAIL'}
STATUS: {evaluation.get('status', 'INCOMPLETE')}
SUMMARY: {evaluation.get('summary', 'No evaluator summary available.')}
NEXT: {evaluation.get('next', 'No next step provided.')}

Current task graph:
```json
{task_graph}
```

Compressed context packet:
{handoff_md}

Base prompt:
{prompt_md}

Current PRD:
{prd_md}

Current summary:
{summary_md}

Steering:
{steering_block}
"""


def run_goal_evaluator(
    *,
    config: dict[str, Any],
    state_dir: Path,
    project_root: Path,
    label: str,
    task: dict[str, Any] | None,
    task_body: dict[str, Any] | None,
    checks_summary: str,
    review_summary: str,
) -> dict[str, Any]:
    command_value = config.get("evaluator", {}).get("command") or config["agent"]["review_command"]
    eval_last_message = state_dir / "evals" / f"{label}-last.md"
    eval_log = state_dir / "evals" / f"{label}.log"
    eval_prompt = build_goal_eval_prompt(
        config=config,
        state_dir=state_dir,
        task=task,
        task_body=task_body,
        checks_summary=checks_summary,
        review_summary=review_summary,
    )
    eval_result = run_codex(
        prompt=eval_prompt,
        command_value=command_value,
        project_root=project_root,
        output_last_message=eval_last_message,
        log_path=eval_log,
        extra_env=config["agent"].get("env", {}),
    )
    return parse_evaluator_result(eval_result["last_message"])


def run_task_replan(
    *,
    config: dict[str, Any],
    state_dir: Path,
    project_root: Path,
    label: str,
    steering_text: str,
    git_available: bool,
    evaluation: dict[str, Any],
) -> dict[str, Any]:
    replan_last_message = state_dir / "history" / f"{label}-last.md"
    replan_log = state_dir / "history" / f"{label}.log"
    replan_prompt = build_task_replan_prompt(
        config=config,
        state_dir=state_dir,
        steering_text=steering_text,
        git_available=git_available,
        evaluation=evaluation,
    )
    return run_codex(
        prompt=replan_prompt,
        command_value=config["agent"]["command"],
        project_root=project_root,
        output_last_message=replan_last_message,
        log_path=replan_log,
        extra_env=config["agent"].get("env", {}),
    )


def run_codex(
    *,
    prompt: str,
    command_value: Any,
    project_root: Path,
    output_last_message: Path,
    log_path: Path,
    extra_env: dict[str, str] | None = None,
) -> dict[str, Any]:
    context = {
        "project_root": str(project_root),
        "output_last_message": str(output_last_message),
    }
    command = render_command(command_value, context)
    env = os.environ.copy()
    if extra_env:
        env.update({key: str(value) for key, value in extra_env.items()})

    result = subprocess.run(
        command,
        cwd=project_root,
        input=prompt,
        text=True,
        capture_output=True,
        env=env,
    )

    combined = [
        f"$ {' '.join(shlex.quote(part) for part in command)}",
        "",
        "## Prompt",
        prompt,
        "",
        "## Stdout",
        result.stdout,
        "",
        "## Stderr",
        result.stderr,
        "",
        f"## Exit code\n{result.returncode}\n",
    ]
    write_text(log_path, "\n".join(combined))

    last_message = read_text(output_last_message)
    if not last_message:
        last_message = result.stdout.strip()

    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "last_message": last_message,
        "command": command,
    }


def run_checks(
    project_root: Path,
    state_dir: Path,
    iteration: int,
    commands: list[str],
    stop_on_failure: bool,
) -> dict[str, Any]:
    if not commands:
        return {"passed": True, "summary": "No local checks configured.", "results": []}

    results = []
    lines = []
    passed = True
    shell_command = resolve_check_shell()
    for index, command in enumerate(commands, start=1):
        proc = subprocess.run(
            [*shell_command, command],
            cwd=project_root,
            capture_output=True,
            text=True,
        )
        passed = passed and proc.returncode == 0
        results.append(
            {
                "command": command,
                "returncode": proc.returncode,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
            }
        )
        lines.extend(
            [
                f"## Check {index}",
                command,
                "",
                "### Stdout",
                proc.stdout,
                "",
                "### Stderr",
                proc.stderr,
                "",
                f"### Exit code\n{proc.returncode}",
                "",
            ]
        )
        if stop_on_failure and proc.returncode != 0:
            lines.append("### Halted remaining checks because stop_on_failure is enabled.\n")
            break

    write_text(state_dir / "logs" / f"iteration-{iteration:03d}-checks.log", "\n".join(lines))
    summary = "All local checks passed." if passed else "One or more local checks failed."
    return {"passed": passed, "summary": summary, "results": results}


def append_loop_log(
    state_dir: Path,
    *,
    iteration: int,
    task: dict[str, Any] | None,
    promise: str,
    checks_summary: str,
    review_summary: str,
    eval_summary: str,
    message: str,
) -> None:
    log_path = state_dir / "logs" / "LOG.md"
    if not log_path.exists():
        write_text(log_path, "# Loop Log\n")

    entry = [
        f"## Iteration {iteration} - {now_iso()}",
        f"- Task: {task.get('id')} {task.get('title')}" if task else "- Task: none",
        f"- Promise: {promise or 'none'}",
        f"- Checks: {checks_summary}",
        f"- Review: {review_summary}",
        f"- Goal Eval: {eval_summary}",
        f"- Summary: {message or 'No assistant summary captured.'}",
        "",
    ]
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(entry))


def ensure_state_dirs(state_dir: Path) -> None:
    for rel in ["history", "reviews", "evals", "artifacts", "logs", "prd", "tasks", "assets", "preflight", "context"]:
        (state_dir / rel).mkdir(parents=True, exist_ok=True)


def maybe_refresh_context(project_root: Path, state_dir: Path, config: dict[str, Any], source: str) -> None:
    if not bool(config.get("context", {}).get("enabled", True)):
        return
    refresh_each_iteration = bool(config.get("context", {}).get("refresh_each_iteration", True))
    if source.startswith("iteration-") and not refresh_each_iteration:
        return
    refresh_context(project_root, state_dir, source=source)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the SummitHarness Codex loop.")
    parser.add_argument("-n", "--max-iterations", type=int, help="Override max iterations")
    parser.add_argument("--once", action="store_true", help="Run exactly one iteration")
    parser.add_argument("--mode", help="Override loop mode")
    parser.add_argument("--state-dir", default=".codex-loop", help="Loop state directory")
    parser.add_argument("--agent-cmd", help="Override worker command")
    parser.add_argument("--review-cmd", help="Override review command")
    parser.add_argument("--skip-review", action="store_true", help="Skip review gate")
    parser.add_argument("--skip-checks", action="store_true", help="Skip local checks")
    args = parser.parse_args()

    project_root = Path.cwd().resolve()
    state_dir = (project_root / args.state_dir).resolve()
    ensure_state_dirs(state_dir)
    ensure_context_layout(project_root, state_dir)
    config = load_config(project_root, state_dir, args)
    git_available = in_git_repo(project_root)

    max_iterations = int(config["loop"]["max_iterations"])
    review_enabled = bool(config["review"].get("enabled", True)) and not args.skip_review
    evaluator_enabled = bool(config.get("evaluator", {}).get("enabled", True))
    evaluator_required = bool(config.get("evaluator", {}).get("require_pass_for_completion", True))
    check_commands = [] if args.skip_checks else list(config["checks"].get("commands", []))
    stop_on_failure = bool(config["checks"].get("stop_on_failure", True))

    try:
        tasks_index = load_tasks_index(state_dir)
        tasks = tasks_index.get("tasks", [])
        if not isinstance(tasks, list):
            raise ValueError(".codex-loop/tasks.json must contain a 'tasks' array")
    except Exception as exc:
        print(f"failed to load tasks: {exc}", file=sys.stderr)
        return ERROR_EXIT

    maybe_refresh_context(project_root, state_dir, config, "loop-start")

    if bool(config["loop"].get("auto_seed_tasks", True)) and tasks_need_seed(tasks_index, tasks):
        seed_last_message = state_dir / "history" / "seed-worker-last.md"
        seed_log = state_dir / "history" / "seed-worker.log"
        steering_text = active_steering(read_text(state_dir / "STEERING.md"))
        seed_prompt = build_task_seed_prompt(
            config=config,
            state_dir=state_dir,
            steering_text=steering_text,
            git_available=git_available,
        )
        seed_result = run_codex(
            prompt=seed_prompt,
            command_value=config["agent"]["command"],
            project_root=project_root,
            output_last_message=seed_last_message,
            log_path=seed_log,
            extra_env=config["agent"].get("env", {}),
        )
        seed_promise = parse_promise(seed_result["last_message"])
        maybe_refresh_context(project_root, state_dir, config, "task-seed-complete")
        tasks_index = load_tasks_index(state_dir)
        tasks = tasks_index.get("tasks", [])
        if seed_promise.startswith("BLOCKED:"):
            print(f"Task bootstrap blocked: {seed_promise}")
            return BLOCKED_EXIT
        if seed_promise.startswith("DECIDE:"):
            print(f"Task bootstrap needs a decision: {seed_promise}")
            return DECIDE_EXIT
        if tasks_need_seed(tasks_index, tasks):
            print("Task bootstrap did not produce a usable task graph.", file=sys.stderr)
            return ERROR_EXIT
        append_loop_log(
            state_dir,
            iteration=0,
            task=None,
            promise=seed_promise or "seeded",
            checks_summary="Not run.",
            review_summary="Not run.",
            eval_summary="Not run.",
            message=first_nonempty_line(seed_result["last_message"]) or "Task graph bootstrap completed.",
        )

    if all_tasks_complete(tasks):
        evaluation = {
            "passed": True,
            "status": "COMPLETE",
            "summary": "Goal evaluator skipped.",
            "next": "No evaluator configured.",
        }
        if evaluator_enabled:
            evaluation = run_goal_evaluator(
                config=config,
                state_dir=state_dir,
                project_root=project_root,
                label="precomplete-eval",
                task=None,
                task_body=None,
                checks_summary="Not run.",
                review_summary="Not run.",
            )
            write_json(
                state_dir / "state.json",
                {
                    "updatedAt": now_iso(),
                    "iteration": 0,
                    "maxIterations": max_iterations,
                    "promise": "",
                    "task": None,
                    "checksPassed": True,
                    "checksSummary": "Not run.",
                    "reviewPassed": True,
                    "reviewSummary": "Not run.",
                    "evalPassed": bool(evaluation.get("passed")),
                    "evalStatus": evaluation.get("status", "INCOMPLETE"),
                    "evalSummary": evaluation.get("summary", "No evaluator summary."),
                    "allTasksComplete": all_tasks_complete(tasks),
                    "gitAvailable": git_available,
                },
            )
            maybe_refresh_context(project_root, state_dir, config, "precomplete-eval")
            if str(evaluation.get("status", "")).upper() == "BLOCKED":
                print(f"Goal evaluator blocked completion: {evaluation.get('summary', '')}")
                return BLOCKED_EXIT
            if str(evaluation.get("status", "")).upper() == "DECIDE":
                print(f"Goal evaluator needs a decision: {evaluation.get('summary', '')}")
                return DECIDE_EXIT
            if not bool(evaluation.get("passed")):
                if should_auto_extend_tasks(tasks, evaluation, config):
                    steering_text = active_steering(read_text(state_dir / "STEERING.md"))
                    replan_result = run_task_replan(
                        config=config,
                        state_dir=state_dir,
                        project_root=project_root,
                        label="precomplete-replan",
                        steering_text=steering_text,
                        git_available=git_available,
                        evaluation=evaluation,
                    )
                    replan_promise = parse_promise(replan_result["last_message"])
                    maybe_refresh_context(project_root, state_dir, config, "precomplete-replan")
                    tasks = load_tasks(state_dir)
                    if replan_promise.startswith("BLOCKED:"):
                        print(f"Task replan blocked: {replan_promise}")
                        return BLOCKED_EXIT
                    if replan_promise.startswith("DECIDE:"):
                        print(f"Task replan needs a decision: {replan_promise}")
                        return DECIDE_EXIT
                    if all_tasks_complete(tasks):
                        print("Goal evaluator found remaining work, but task replan did not open any actionable tasks.", file=sys.stderr)
                        return ERROR_EXIT
                else:
                    print(f"All tasks are marked complete, but the goal evaluator says the goal is not yet met: {evaluation.get('summary', '')}")
                    return DECIDE_EXIT
        if all_tasks_complete(tasks):
            print("All tasks are already complete.")
            maybe_refresh_context(project_root, state_dir, config, "loop-complete")
            return COMPLETE_EXIT

    for iteration in range(1, max_iterations + 1):
        tasks = load_tasks(state_dir)
        specs = load_task_specs(state_dir, tasks)
        task = select_task(tasks, specs)
        task_body = specs.get(str(task.get("id"))) if task else None
        maybe_refresh_context(project_root, state_dir, config, f"iteration-{iteration}-before")

        if task is None and not all_tasks_complete(tasks):
            blocked = blocked_tasks(tasks, specs)
            summary = "No runnable task was found. Dependencies may be unresolved or cyclic."
            append_loop_log(
                state_dir,
                iteration=iteration,
                task=None,
                promise="DECIDE:dependency-order",
                checks_summary="Not run.",
                review_summary="Not run.",
                eval_summary="Not run.",
                message=summary,
            )
            state_payload = {
                "updatedAt": now_iso(),
                "iteration": iteration,
                "maxIterations": max_iterations,
                "promise": "DECIDE:dependency-order",
                "task": None,
                "checksPassed": False,
                "checksSummary": "Not run.",
                "reviewPassed": False,
                "reviewSummary": "Not run.",
                "evalPassed": False,
                "evalStatus": "INCOMPLETE",
                "evalSummary": "Not run.",
                "allTasksComplete": False,
                "gitAvailable": git_available,
                "blockedTasks": blocked,
            }
            write_json(state_dir / "state.json", state_payload)
            maybe_refresh_context(project_root, state_dir, config, f"iteration-{iteration}-blocked")
            print(summary)
            return DECIDE_EXIT

        worker_last_message = state_dir / "history" / f"iteration-{iteration:03d}-worker-last.md"
        worker_log = state_dir / "history" / f"iteration-{iteration:03d}-worker.log"
        steering_text = active_steering(read_text(state_dir / "STEERING.md"))
        worker_prompt = build_worker_prompt(
            config=config,
            state_dir=state_dir,
            iteration=iteration,
            task=task,
            task_body=task_body,
            steering_text=steering_text,
            git_available=git_available,
        )
        worker_result = run_codex(
            prompt=worker_prompt,
            command_value=config["agent"]["command"],
            project_root=project_root,
            output_last_message=worker_last_message,
            log_path=worker_log,
            extra_env=config["agent"].get("env", {}),
        )

        promise = parse_promise(worker_result["last_message"])
        checks = run_checks(project_root, state_dir, iteration, check_commands, stop_on_failure)

        review_summary = "Skipped."
        review_passed = True
        if review_enabled and checks["passed"]:
            review_last_message = state_dir / "reviews" / f"iteration-{iteration:03d}-review-last.md"
            review_log = state_dir / "reviews" / f"iteration-{iteration:03d}-review.log"
            review_prompt = build_review_prompt(
                config=config,
                state_dir=state_dir,
                task=task,
                task_body=task_body,
                checks_summary=checks["summary"],
            )
            review_result = run_codex(
                prompt=review_prompt,
                command_value=config["agent"]["review_command"],
                project_root=project_root,
                output_last_message=review_last_message,
                log_path=review_log,
            )
            review_passed, review_summary = parse_review_result(review_result["last_message"])
        elif review_enabled:
            review_passed = False
            review_summary = "Skipped because local checks failed."

        tasks, specs, active_task, active_task_body = load_current_task_snapshot(state_dir)
        interim_state_payload = {
            "updatedAt": now_iso(),
            "iteration": iteration,
            "maxIterations": max_iterations,
            "promise": promise,
            "task": active_task,
            "checksPassed": checks["passed"],
            "checksSummary": checks["summary"],
            "reviewPassed": review_passed,
            "reviewSummary": review_summary,
            "evalPassed": False,
            "evalStatus": "INCOMPLETE",
            "evalSummary": "Pending goal evaluation for this iteration.",
            "evalNext": "",
            "allTasksComplete": all_tasks_complete(tasks),
            "gitAvailable": git_available,
            "replanSummary": "",
        }
        write_json(state_dir / "state.json", interim_state_payload)
        maybe_refresh_context(project_root, state_dir, config, f"iteration-{iteration}-pre-eval")

        evaluation = {
            "passed": True,
            "status": "COMPLETE",
            "summary": "Goal evaluator skipped.",
            "next": "No evaluator configured.",
        }
        if evaluator_enabled:
            evaluation = run_goal_evaluator(
                config=config,
                state_dir=state_dir,
                project_root=project_root,
                label=f"iteration-{iteration:03d}-eval",
                task=active_task,
                task_body=active_task_body,
                checks_summary=checks["summary"],
                review_summary=review_summary,
            )

        tasks, specs, active_task, active_task_body = load_current_task_snapshot(state_dir)
        replan_summary = ""
        replan_signal = ""
        if should_auto_extend_tasks(tasks, evaluation, config):
            replan_result = run_task_replan(
                config=config,
                state_dir=state_dir,
                project_root=project_root,
                label=f"iteration-{iteration:03d}-replan",
                steering_text=steering_text,
                git_available=git_available,
                evaluation=evaluation,
            )
            replan_signal = parse_promise(replan_result["last_message"])
            maybe_refresh_context(project_root, state_dir, config, f"iteration-{iteration}-replan")
            tasks, specs, active_task, active_task_body = load_current_task_snapshot(state_dir)
            replan_summary = first_nonempty_line(replan_result["last_message"]) or "Task graph refreshed after evaluator failure."
            if all_tasks_complete(tasks) and not replan_signal.startswith(("BLOCKED:", "DECIDE:")):
                print("Goal evaluator found remaining work, but task replan did not open any actionable tasks.", file=sys.stderr)
                return ERROR_EXIT

        require_eval_pass = evaluator_enabled and evaluator_required
        eval_summary = evaluation.get("summary", "No evaluator summary.")
        if replan_summary:
            eval_summary = f"{eval_summary} Replan: {replan_summary}"
        finished = all_tasks_complete(tasks) and checks["passed"] and review_passed and (not require_eval_pass or (bool(evaluation.get("passed")) and str(evaluation.get("status", "COMPLETE")).upper() == "COMPLETE"))
        state_payload = {
            "updatedAt": now_iso(),
            "iteration": iteration,
            "maxIterations": max_iterations,
            "promise": promise,
            "task": active_task,
            "checksPassed": checks["passed"],
            "checksSummary": checks["summary"],
            "reviewPassed": review_passed,
            "reviewSummary": review_summary,
            "evalPassed": bool(evaluation.get("passed")),
            "evalStatus": evaluation.get("status", "INCOMPLETE"),
            "evalSummary": eval_summary,
            "evalNext": evaluation.get("next", ""),
            "allTasksComplete": all_tasks_complete(tasks),
            "gitAvailable": git_available,
            "replanSummary": replan_summary,
        }
        write_json(state_dir / "state.json", state_payload)

        loop_message = first_nonempty_line(worker_result["last_message"])
        if replan_summary:
            loop_message = (loop_message + " " + replan_summary).strip()

        append_loop_log(
            state_dir,
            iteration=iteration,
            task=task,
            promise=promise,
            checks_summary=checks["summary"],
            review_summary=review_summary,
            eval_summary=eval_summary,
            message=loop_message,
        )
        maybe_refresh_context(project_root, state_dir, config, f"iteration-{iteration}-after")

        print(f"[iteration {iteration}] task={task.get('id') if task else 'none'}")
        print(f"[iteration {iteration}] checks={checks['summary']}")
        print(f"[iteration {iteration}] review={review_summary}")
        print(f"[iteration {iteration}] goal-eval={eval_summary}")
        if promise:
            print(f"[iteration {iteration}] promise={promise}")

        if promise.startswith("BLOCKED:") or replan_signal.startswith("BLOCKED:") or str(evaluation.get("status", "")).upper() == "BLOCKED":
            return BLOCKED_EXIT
        if promise.startswith("DECIDE:") or replan_signal.startswith("DECIDE:") or str(evaluation.get("status", "")).upper() == "DECIDE":
            return DECIDE_EXIT
        if promise == config["loop"]["completion_promise"] and finished:
            print("Loop completed with a valid completion promise.")
            maybe_refresh_context(project_root, state_dir, config, "loop-complete")
            return COMPLETE_EXIT
        if finished:
            print("Loop completed because tasks, checks, review, and goal evaluation all passed.")
            maybe_refresh_context(project_root, state_dir, config, "loop-complete")
            return COMPLETE_EXIT

    maybe_refresh_context(project_root, state_dir, config, "loop-max-iterations")
    print(f"Reached max iterations ({max_iterations}).")
    return MAX_ITER_EXIT


if __name__ == "__main__":
    raise SystemExit(main())
