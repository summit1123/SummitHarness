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
PRIORITY_ORDER = {"p0": 0, "p1": 1, "p2": 2, "p3": 3}

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
    },
    "checks": {
        "commands": [],
        "stop_on_failure": True,
    },
    "review": {
        "enabled": True,
        "max_findings": 5,
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


def load_tasks(state_dir: Path) -> list[dict[str, Any]]:
    tasks_index = load_json(state_dir / "tasks.json")
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
    return str(task.get("status", "")).lower() in {"done", "skipped"}


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

    todo = [task for task in tasks if str(task.get("status", "")).lower() == "todo"]
    ready_todo = [task for task in todo if task_is_ready(task, specs, done_ids)]
    if ready_todo:
        return sorted(ready_todo, key=task_sort_key)[0]
    return None


def blocked_tasks(tasks: list[dict[str, Any]], specs: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    done_ids = {str(task.get("id")) for task in tasks if task_is_done(task)}
    pending = [task for task in tasks if str(task.get("status", "")).lower() in {"todo", "in_progress"}]
    return [task for task in pending if not task_is_ready(task, specs, done_ids)]


def all_tasks_complete(tasks: list[dict[str, Any]]) -> bool:
    return bool(tasks) and all(task_is_done(task) for task in tasks)


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


def first_nonempty_line(text: str, limit: int = 160) -> str:
    for line in (text or "").splitlines():
        line = line.strip()
        if line:
            return line[:limit]
    return ""


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
        f"- Summary: {message or 'No assistant summary captured.'}",
        "",
    ]
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(entry))


def ensure_state_dirs(state_dir: Path) -> None:
    for rel in ["history", "reviews", "artifacts", "logs", "prd", "tasks", "assets", "preflight", "context"]:
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
    check_commands = [] if args.skip_checks else list(config["checks"].get("commands", []))
    stop_on_failure = bool(config["checks"].get("stop_on_failure", True))

    try:
        tasks = load_tasks(state_dir)
    except Exception as exc:
        print(f"failed to load tasks: {exc}", file=sys.stderr)
        return ERROR_EXIT

    maybe_refresh_context(project_root, state_dir, config, "loop-start")

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

        tasks = load_tasks(state_dir)
        finished = all_tasks_complete(tasks) and checks["passed"] and review_passed
        state_payload = {
            "updatedAt": now_iso(),
            "iteration": iteration,
            "maxIterations": max_iterations,
            "promise": promise,
            "task": task,
            "checksPassed": checks["passed"],
            "checksSummary": checks["summary"],
            "reviewPassed": review_passed,
            "reviewSummary": review_summary,
            "allTasksComplete": all_tasks_complete(tasks),
            "gitAvailable": git_available,
        }
        write_json(state_dir / "state.json", state_payload)

        append_loop_log(
            state_dir,
            iteration=iteration,
            task=task,
            promise=promise,
            checks_summary=checks["summary"],
            review_summary=review_summary,
            message=first_nonempty_line(worker_result["last_message"]),
        )
        maybe_refresh_context(project_root, state_dir, config, f"iteration-{iteration}-after")

        print(f"[iteration {iteration}] task={task.get('id') if task else 'none'}")
        print(f"[iteration {iteration}] checks={checks['summary']}")
        print(f"[iteration {iteration}] review={review_summary}")
        if promise:
            print(f"[iteration {iteration}] promise={promise}")

        if promise.startswith("BLOCKED:"):
            return BLOCKED_EXIT
        if promise.startswith("DECIDE:"):
            return DECIDE_EXIT
        if promise == config["loop"]["completion_promise"] and finished:
            print("Loop completed with a valid completion promise.")
            maybe_refresh_context(project_root, state_dir, config, "loop-complete")
            return COMPLETE_EXIT
        if finished:
            print("Loop completed because all tasks, checks, and review gates passed.")
            maybe_refresh_context(project_root, state_dir, config, "loop-complete")
            return COMPLETE_EXIT

    maybe_refresh_context(project_root, state_dir, config, "loop-max-iterations")
    print(f"Reached max iterations ({max_iterations}).")
    return MAX_ITER_EXIT


if __name__ == "__main__":
    raise SystemExit(main())
