from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import textwrap
import unittest
from unittest import mock
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = REPO_ROOT / "plugins" / "codex-ralph-loop" / "scripts" / "bootstrap_project.py"
STOP_DISPATCH = REPO_ROOT / "plugins" / "codex-ralph-loop" / "scripts" / "stop_hook_dispatch.py"
CODEX_RALPH = REPO_ROOT / "plugins" / "codex-ralph-loop" / "templates" / "project" / "scripts" / "codex_ralph.py"
CONTEXT_ENGINE = REPO_ROOT / "plugins" / "codex-ralph-loop" / "templates" / "project" / "scripts" / "context_engine.py"
REVIEW_PDF = REPO_ROOT / "plugins" / "codex-ralph-loop" / "templates" / "project" / "scripts" / "review_submission_pdf.py"
INSTALLER = REPO_ROOT / "plugins" / "codex-ralph-loop" / "scripts" / "install_home_local.py"
PLUGIN_COMMANDS_DIR = REPO_ROOT / "plugins" / "codex-ralph-loop" / "commands"


def load_module(path: Path, name: str):
    if str(path.parent) not in sys.path:
        sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class SummitHarnessTests(unittest.TestCase):
    def test_bootstrap_preserves_existing_codex_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            (root / ".codex").mkdir(parents=True, exist_ok=True)
            marker = root / ".codex" / "existing.txt"
            marker.write_text("keep", encoding="utf-8")
            subprocess.run([sys.executable, str(BOOTSTRAP), "--force", str(root)], check=True)
            self.assertTrue(marker.exists())
            self.assertTrue((root / "scripts" / "context_engine.py").exists())
            self.assertTrue((root / "scripts" / "review_submission_pdf.py").exists())
            self.assertTrue((root / ".codex-loop" / "context" / "durable.json").exists())
            self.assertTrue((root / ".codex-loop" / "evals" / ".gitkeep").exists())

    def test_context_and_asset_smoke(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run([sys.executable, str(BOOTSTRAP), str(root)], check=True)
            subprocess.run([sys.executable, str(root / "scripts" / "context_engine.py"), "refresh", "--source", "test"], cwd=root, check=True)
            subprocess.run(
                [
                    sys.executable,
                    str(root / "scripts" / "asset_registry.py"),
                    "add",
                    "--kind",
                    "image",
                    "--path",
                    "assets/hero-v1.png",
                    "--source",
                    "imagegen",
                    "--status",
                    "approved",
                    "--title",
                    "Hero v1",
                ],
                cwd=root,
                check=True,
            )
            subprocess.run([sys.executable, str(root / "scripts" / "context_engine.py"), "refresh", "--source", "asset"], cwd=root, check=True)
            status = subprocess.run(
                [sys.executable, str(root / "scripts" / "context_engine.py"), "status", "--json"],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(status.stdout)
            self.assertIn("Hero v1", "\n".join(payload["approvedAssets"]))
            self.assertIn("nextBestStep", payload)
            self.assertIn("auto-generate the real task graph", payload["nextBestStep"])

    def test_stop_hook_does_not_accept_completion_mention_when_tasks_are_open(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".codex-loop" / "logs").mkdir(parents=True, exist_ok=True)
            (root / ".codex-loop" / "tasks.json").write_text('{"tasks":[{"id":"001","status":"todo"}]}\n', encoding="utf-8")
            (root / ".codex-loop" / "ralph-loop.json").write_text(
                json.dumps(
                    {
                        "active": True,
                        "prompt": "Do the work.",
                        "completionPromise": "<promise>COMPLETE</promise>",
                        "maxIterations": 20,
                        "currentIteration": 0,
                        "requireTaskCompletion": True,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, str(STOP_DISPATCH)],
                input=json.dumps(
                    {
                        "cwd": str(root),
                        "turn_id": "t1",
                        "stop_hook_active": False,
                        "last_assistant_message": "I will emit <promise>COMPLETE</promise> when I am really done.",
                    }
                ),
                text=True,
                capture_output=True,
                check=True,
            )
            state = json.loads((root / ".codex-loop" / "ralph-loop.json").read_text(encoding="utf-8"))
            self.assertTrue(state["active"])
            self.assertEqual(state["currentIteration"], 1)
            self.assertIn('"decision": "block"', result.stdout)

    def test_dependency_selection_and_stop_on_failure(self) -> None:
        mod = load_module(CODEX_RALPH, "codex_ralph_test")
        tasks = [
            {"id": "002", "status": "todo", "priority": "p0", "title": "B"},
            {"id": "001", "status": "todo", "priority": "p1", "title": "A"},
        ]
        specs = {"002": {"dependsOn": ["001"]}, "001": {"dependsOn": []}}
        selected = mod.select_task(tasks, specs)
        self.assertEqual(selected["id"], "001")

        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            (state_dir / "logs").mkdir(parents=True, exist_ok=True)
            result = mod.run_checks(REPO_ROOT, state_dir, 1, ["false", "echo second-check-ran"], True)
            log_text = (state_dir / "logs" / "iteration-001-checks.log").read_text(encoding="utf-8")
            self.assertFalse(result["passed"])
            self.assertNotIn("second-check-ran", log_text)
            self.assertIn("Halted remaining checks", log_text)

    def test_resolve_check_shell_falls_back_to_bash_when_zsh_is_missing(self) -> None:
        mod = load_module(CODEX_RALPH, "codex_ralph_shell_test")

        def fake_exists(path: str) -> bool:
            return path == "/bin/bash"

        with mock.patch.dict(mod.os.environ, {}, clear=True):
            with mock.patch.object(mod.os.path, "exists", side_effect=fake_exists):
                with mock.patch.object(mod.shutil, "which", return_value=None):
                    self.assertEqual(mod.resolve_check_shell(), ["/bin/bash", "-lc"])

    def test_parse_evaluator_result_understands_pass_and_fail(self) -> None:
        mod = load_module(CODEX_RALPH, "codex_ralph_eval_test")
        passed = mod.parse_evaluator_result("""RESULT: PASS
STATUS: COMPLETE
SUMMARY: Goal is satisfied.
NEXT: Ship it.
REPLAN: NO
""")
        self.assertTrue(passed["passed"])
        self.assertEqual(passed["status"], "COMPLETE")
        self.assertEqual(passed["summary"], "Goal is satisfied.")
        self.assertFalse(passed["replan"])

        failed = mod.parse_evaluator_result("""RESULT: FAIL
STATUS: INCOMPLETE
SUMMARY: Missing tests.
NEXT: Add tests.
REPLAN: YES
""")
        self.assertFalse(failed["passed"])
        self.assertEqual(failed["status"], "INCOMPLETE")
        self.assertEqual(failed["next"], "Add tests.")
        self.assertTrue(failed["replan"])

    def test_should_auto_extend_tasks_when_evaluator_detects_task_graph_drift(self) -> None:
        mod = load_module(CODEX_RALPH, "codex_ralph_replan_test")
        config = {
            "evaluator": {
                "enabled": True,
                "auto_extend_tasks": True,
            }
        }
        tasks = [
            {"id": "005", "status": "done", "priority": "p0", "title": "Why now"},
            {"id": "006", "status": "in_progress", "priority": "p0", "title": "Structure"},
        ]
        evaluation = {
            "passed": False,
            "status": "INCOMPLETE",
            "replan": True,
        }
        self.assertTrue(mod.should_auto_extend_tasks(tasks, evaluation, config))

    def test_select_task_accepts_pending_status_as_next_work(self) -> None:
        mod = load_module(CODEX_RALPH, "codex_ralph_pending_test")
        tasks = [
            {"id": "001", "status": "done", "priority": "p0", "title": "Locked"},
            {"id": "002", "status": "pending", "priority": "p0", "title": "Smoke"},
        ]
        specs = {"001": {"dependsOn": []}, "002": {"dependsOn": ["001"]}}
        selected = mod.select_task(tasks, specs)
        self.assertIsNotNone(selected)
        self.assertEqual(selected["id"], "002")

    def test_select_task_accepts_completed_status_as_done(self) -> None:
        mod = load_module(CODEX_RALPH, "codex_ralph_completed_test")
        tasks = [
            {"id": "001", "status": "completed", "priority": "p0", "title": "Audit"},
            {"id": "002", "status": "todo", "priority": "p0", "title": "Draft"},
        ]
        specs = {"001": {"dependsOn": []}, "002": {"dependsOn": ["001"]}}
        selected = mod.select_task(tasks, specs)
        self.assertIsNotNone(selected)
        self.assertEqual(selected["id"], "002")

    def test_tasks_need_seed_detects_bootstrap_template(self) -> None:
        mod = load_module(CODEX_RALPH, "codex_ralph_seed_test")
        tasks_index = {
            "project": "Codex Ralph Loop Workspace",
            "source": "bootstrap-template",
            "tasks": [
                {"id": "001", "title": "Brainstorm and lock the build brief", "status": "todo"},
                {"id": "002", "title": "Write the first execution plan", "status": "todo"},
                {"id": "003", "title": "Build and verify the first vertical slice", "status": "todo"},
            ],
        }
        self.assertTrue(mod.tasks_need_seed(tasks_index, tasks_index["tasks"]))

        custom_index = {
            "project": "MIRROR contest submission planning workspace",
            "tasks": [
                {"id": "001", "title": "Audit current MIRROR reality and contest constraints", "status": "todo"},
                {"id": "002", "title": "Draft the Korean web-form submission answers", "status": "todo"},
            ],
        }
        self.assertFalse(mod.tasks_need_seed(custom_index, custom_index["tasks"]))

    def test_submission_pdf_review_writes_report_and_flags_bad_filename(self) -> None:
        mod = load_module(REVIEW_PDF, "review_submission_pdf_test")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            pdf_path = root / "proposal,draft.pdf"
            pdf_path.write_bytes(b"%PDF-1.4\n%stub\n")

            with mock.patch.object(
                mod,
                "probe_pdf",
                return_value={
                    "available": True,
                    "method": "pdfinfo",
                    "pages": 8,
                    "pageSize": "596 x 843 pts",
                    "pdfVersion": "1.4",
                },
            ):
                with mock.patch.object(
                    mod,
                    "extract_preview_text",
                    return_value={
                        "available": True,
                        "method": "pdftotext",
                        "preview": "Contest preview text",
                        "charCount": 20,
                        "error": None,
                    },
                ):
                    review = mod.build_review(root, pdf_path, 20.0)
                    json_path, md_path = mod.write_review_files(root, review)

            self.assertTrue(any("comma" in item.lower() for item in review["blockers"]))
            self.assertEqual(review["metadata"]["pages"], 8)
            self.assertEqual(review["extraction"]["preview"], "Contest preview text")
            self.assertTrue(json_path.exists())
            self.assertTrue(md_path.exists())

    def test_context_engine_surfaces_latest_submission_pdf_review(self) -> None:
        mod = load_module(CONTEXT_ENGINE, "context_engine_pdf_review_test")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            subprocess.run([sys.executable, str(BOOTSTRAP), str(root)], check=True)
            review_dir = root / ".codex-loop" / "artifacts" / "pdf-review"
            review_dir.mkdir(parents=True, exist_ok=True)
            (review_dir / "proposal-review.json").write_text(
                json.dumps(
                    {
                        "file": {"name": "proposal.pdf", "sizeMegabytes": 0.4},
                        "metadata": {"pages": 8},
                        "blockers": ["Rename the file."],
                        "warnings": [],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            status = mod.load_status(root, root / ".codex-loop")
            self.assertIn("proposal.pdf", status["handoff"])
            self.assertIn("submission pdf blockers", status["nextBestStep"].lower())

    def test_loop_can_replan_after_goal_evaluator_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run([sys.executable, str(BOOTSTRAP), str(root)], check=True)

            stub = root / "stub_agent.py"
            stub.write_text(
                r"""#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_last(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8")


def mark_task(root: Path, task_id: str, status: str) -> None:
    tasks_path = root / ".codex-loop" / "tasks.json"
    index = load_json(tasks_path, {})
    for task in index.get("tasks", []):
        if str(task.get("id")) == task_id:
            task["status"] = status
    write_json(tasks_path, index)

    task_path = root / ".codex-loop" / "tasks" / f"TASK-{task_id}.json"
    task_payload = load_json(task_path, {"id": task_id})
    task_payload["status"] = status
    write_json(task_path, task_payload)


def seed_graph(root: Path) -> None:
    state_dir = root / ".codex-loop"
    write_json(
        state_dir / "tasks.json",
        {
            "project": "Stub Integration Project",
            "selection": "priority-order",
            "tasks": [
                {
                    "id": "001",
                    "title": "Build initial slice",
                    "status": "todo",
                    "priority": "p0",
                    "file": "tasks/TASK-001.json",
                }
            ],
        },
    )
    write_json(
        state_dir / "tasks" / "TASK-001.json",
        {
            "id": "001",
            "title": "Build initial slice",
            "status": "todo",
            "priority": "p0",
            "dependsOn": [],
            "deliverables": ["app.txt"],
            "acceptance": ["Create the first partial artifact."],
        },
    )


def replan_graph(root: Path) -> None:
    state_dir = root / ".codex-loop"
    index = load_json(state_dir / "tasks.json", {})
    tasks = index.get("tasks", [])
    have_001 = any(str(task.get("id")) == "001" for task in tasks)
    have_002 = any(str(task.get("id")) == "002" for task in tasks)
    if not have_001:
        tasks.append({
            "id": "001",
            "title": "Build initial slice",
            "status": "completed",
            "priority": "p0",
            "file": "tasks/TASK-001.json",
        })
    for task in tasks:
        if str(task.get("id")) == "001":
            task["status"] = "completed"
    if not have_002:
        tasks.append({
            "id": "002",
            "title": "Finish the goal",
            "status": "todo",
            "priority": "p0",
            "file": "tasks/TASK-002.json",
        })
    index["tasks"] = tasks
    write_json(state_dir / "tasks.json", index)
    write_json(
        state_dir / "tasks" / "TASK-002.json",
        {
            "id": "002",
            "title": "Finish the goal",
            "status": "todo",
            "priority": "p0",
            "dependsOn": ["001"],
            "deliverables": ["app.txt"],
            "acceptance": ["Finalize the artifact so the goal truly passes."],
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True, choices=["worker", "review", "evaluator"])
    parser.add_argument("output_last_message")
    args = parser.parse_args()

    prompt = sys.stdin.read()
    root = Path.cwd()

    if args.mode == "review":
        write_last(Path(args.output_last_message), "RESULT: PASS\nSUMMARY: Stub review passed.\nFINDINGS:\n- none")
        return 0

    if args.mode == "evaluator":
        app_text = (root / "app.txt").read_text(encoding="utf-8").strip() if (root / "app.txt").exists() else ""
        tasks = load_json(root / ".codex-loop" / "tasks.json", {}).get("tasks", [])
        all_done = tasks and all(str(task.get("status", "")).lower() in {"done", "completed", "complete", "skipped"} for task in tasks)
        have_002 = any(str(task.get("id")) == "002" for task in tasks)
        if all_done and have_002 and app_text == "final":
            write_last(Path(args.output_last_message), "RESULT: PASS\nSTATUS: COMPLETE\nSUMMARY: Goal satisfied with a truthful final artifact.\nNEXT: Ship it.\nMISSING:\n- none")
        elif all_done:
            write_last(Path(args.output_last_message), "RESULT: FAIL\nSTATUS: INCOMPLETE\nSUMMARY: The task list says done, but the goal is still not fully met.\nNEXT: Replan the remaining work.\nMISSING:\n- final artifact still incomplete")
        else:
            write_last(Path(args.output_last_message), "RESULT: FAIL\nSTATUS: INCOMPLETE\nSUMMARY: Work is still in progress.\nNEXT: Continue the current task graph.\nMISSING:\n- open tasks remain")
        return 0

    if "initializing the SummitHarness task graph for the first real loop run" in prompt:
        seed_graph(root)
        write_last(Path(args.output_last_message), "<promise>COMPLETE</promise>\nSeeded initial task graph.")
        return 0

    if "refreshing the SummitHarness task graph because the goal evaluator found remaining work" in prompt:
        replan_graph(root)
        write_last(Path(args.output_last_message), "<promise>COMPLETE</promise>\nReplanned the remaining work.")
        return 0

    if '"id": "002"' in prompt or "Finish the goal" in prompt:
        (root / "app.txt").write_text("final\n", encoding="utf-8")
        mark_task(root, "002", "completed")
        write_last(Path(args.output_last_message), "<promise>COMPLETE</promise>\nFinished the remaining work.")
        return 0

    if '"id": "001"' in prompt or "Build initial slice" in prompt:
        (root / "app.txt").write_text("partial\n", encoding="utf-8")
        mark_task(root, "001", "completed")
        write_last(Path(args.output_last_message), "Implemented the initial slice.")
        return 0

    write_last(Path(args.output_last_message), "No-op stub response.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
""",
                encoding="utf-8",
            )

            config_path = root / ".codex-loop" / "config.json"
            config = json.loads(config_path.read_text(encoding="utf-8"))
            config["agent"]["command"] = [sys.executable, str(stub), "--mode", "worker", "{output_last_message}"]
            config["agent"]["review_command"] = [sys.executable, str(stub), "--mode", "review", "{output_last_message}"]
            config["evaluator"]["command"] = [sys.executable, str(stub), "--mode", "evaluator", "{output_last_message}"]
            config["checks"]["commands"] = []
            config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(root / "scripts" / "codex_ralph.py"), "-n", "3"],
                cwd=root,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            tasks_index = json.loads((root / ".codex-loop" / "tasks.json").read_text(encoding="utf-8"))
            statuses = {task["id"]: task["status"] for task in tasks_index["tasks"]}
            self.assertEqual(statuses["001"], "completed")
            self.assertEqual(statuses["002"], "completed")
            self.assertEqual((root / "app.txt").read_text(encoding="utf-8").strip(), "final")
            self.assertTrue((root / ".codex-loop" / "history" / "iteration-001-replan-last.md").exists())
            self.assertTrue((root / ".codex-loop" / "evals" / "iteration-001-eval-last.md").exists())
            log_text = (root / ".codex-loop" / "logs" / "LOG.md").read_text(encoding="utf-8")
            self.assertIn("Goal Eval", log_text)
            self.assertIn("Goal satisfied with a truthful final artifact.", log_text)

    def test_goal_evaluator_sees_refreshed_active_task_after_worker_progress(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            subprocess.run([sys.executable, str(BOOTSTRAP), str(root)], check=True)

            state_dir = root / ".codex-loop"
            (state_dir / "tasks.json").write_text(
                json.dumps(
                    {
                        "project": "State Sync Project",
                        "source": "manual",
                        "tasks": [
                            {
                                "id": "001",
                                "title": "Stabilize the loop",
                                "status": "in_progress",
                                "priority": "p0",
                                "file": "tasks/TASK-001.json",
                            },
                            {
                                "id": "002",
                                "title": "Advance verification",
                                "status": "todo",
                                "priority": "p1",
                                "file": "tasks/TASK-002.json",
                            },
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            (state_dir / "tasks" / "TASK-001.json").write_text(
                json.dumps(
                    {
                        "id": "001",
                        "title": "Stabilize the loop",
                        "status": "in_progress",
                        "priority": "p0",
                        "dependsOn": [],
                        "deliverables": ["notes.md"],
                        "acceptance": ["Move the loop to task 002 truthfully."],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            (state_dir / "tasks" / "TASK-002.json").write_text(
                json.dumps(
                    {
                        "id": "002",
                        "title": "Advance verification",
                        "status": "todo",
                        "priority": "p1",
                        "dependsOn": ["001"],
                        "deliverables": ["notes.md"],
                        "acceptance": ["Evaluator should see task 002 as active once task 001 moves forward."],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            stub = root / "sync_stub.py"
            stub.write_text(
                "\n".join(
                    [
                        '#!/usr/bin/env python3',
                        'from __future__ import annotations',
                        '',
                        'import argparse',
                        'import json',
                        'import sys',
                        'from pathlib import Path',
                        '',
                        '',
                        'def load_json(path: Path, default):',
                        '    if not path.exists():',
                        '        return default',
                        '    return json.loads(path.read_text(encoding="utf-8"))',
                        '',
                        '',
                        'def write_json(path: Path, payload) -> None:',
                        '    path.parent.mkdir(parents=True, exist_ok=True)',
                        '    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")',
                        '',
                        '',
                        'def write_last(path: Path, text: str) -> None:',
                        '    path.parent.mkdir(parents=True, exist_ok=True)',
                        '    path.write_text(text.strip() + "\\n", encoding="utf-8")',
                        '',
                        '',
                        'def mark_task(root: Path, task_id: str, status: str) -> None:',
                        '    tasks_path = root / ".codex-loop" / "tasks.json"',
                        '    index = load_json(tasks_path, {})',
                        '    for task in index.get("tasks", []):',
                        '        if str(task.get("id")) == task_id:',
                        '            task["status"] = status',
                        '    write_json(tasks_path, index)',
                        '',
                        '    task_path = root / ".codex-loop" / "tasks" / f"TASK-{task_id}.json"',
                        '    task_payload = load_json(task_path, {"id": task_id})',
                        '    task_payload["status"] = status',
                        '    write_json(task_path, task_payload)',
                        '',
                        '',
                        'def main() -> int:',
                        '    parser = argparse.ArgumentParser()',
                        '    parser.add_argument("--mode", required=True, choices=["worker", "review", "evaluator"])',
                        '    parser.add_argument("output_last_message")',
                        '    args = parser.parse_args()',
                        '',
                        '    prompt = sys.stdin.read()',
                        '    root = Path.cwd()',
                        '',
                        '    if args.mode == "review":',
                        '        write_last(Path(args.output_last_message), "RESULT: PASS\\nSUMMARY: Stub review passed.\\nFINDINGS:\\n- none")',
                        '        return 0',
                        '',
                        '    if args.mode == "evaluator":',
                        '        active_index_ok = "Active task index entry:\\n```json\\n{\\n  \\"id\\": \\"002\\"" in prompt',
                        '        handoff_ok = "- Active task: 002 Advance verification" in prompt',
                        '        summary = (',
                        '            "Active task stayed in sync after worker progress."',
                        '            if active_index_ok and handoff_ok',
                        '            else "Evaluator saw stale active-task metadata."',
                        '        )',
                        '        write_last(',
                        '            Path(args.output_last_message),',
                        '            f"RESULT: FAIL\\nSTATUS: INCOMPLETE\\nSUMMARY: {summary}\\nNEXT: Continue the current task graph.\\nMISSING:\\n- none",',
                        '        )',
                        '        return 0',
                        '',
                        '    mark_task(root, "001", "completed")',
                        '    mark_task(root, "002", "in_progress")',
                        '    write_last(Path(args.output_last_message), "Moved the loop forward to task 002.")',
                        '    return 0',
                        '',
                        '',
                        'if __name__ == "__main__":',
                        '    raise SystemExit(main())',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            config_path = state_dir / "config.json"
            config = json.loads(config_path.read_text(encoding="utf-8"))
            config["agent"]["command"] = [sys.executable, str(stub), "--mode", "worker", "{output_last_message}"]
            config["agent"]["review_command"] = [sys.executable, str(stub), "--mode", "review", "{output_last_message}"]
            config["evaluator"]["command"] = [sys.executable, str(stub), "--mode", "evaluator", "{output_last_message}"]
            config["checks"]["commands"] = []
            config["review"]["enabled"] = False
            config["loop"]["auto_seed_tasks"] = False
            config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(root / "scripts" / "codex_ralph.py"), "-n", "1"],
                cwd=root,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            state = json.loads((state_dir / "state.json").read_text(encoding="utf-8"))
            self.assertEqual(state["evalSummary"], "Active task stayed in sync after worker progress.")
            self.assertEqual(state["task"]["id"], "002")
            handoff = (state_dir / "context" / "handoff.md").read_text(encoding="utf-8")
            self.assertIn("- Active task: 002 Advance verification", handoff)

    def test_installer_creates_backup_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            plugin_dir = tmp_root / "codex" / "plugins" / "codex-ralph-loop"
            marketplace = tmp_root / "agents" / "plugins" / "marketplace.json"
            user_skills = tmp_root / "agents" / "skills"
            codex_config = tmp_root / "codex" / "config.toml"
            codex_hooks = tmp_root / "codex" / "hooks.json"
            backup_root = tmp_root / "backups" / "install-1"

            plugin_dir.mkdir(parents=True, exist_ok=True)
            (plugin_dir / "old.txt").write_text("old plugin", encoding="utf-8")
            marketplace.parent.mkdir(parents=True, exist_ok=True)
            marketplace.write_text('{"plugins": []}\n', encoding="utf-8")
            codex_config.parent.mkdir(parents=True, exist_ok=True)
            codex_config.write_text('[features]\ncodex_hooks = false\n', encoding="utf-8")
            codex_hooks.parent.mkdir(parents=True, exist_ok=True)
            codex_hooks.write_text('{"hooks": {}}\n', encoding="utf-8")

            subprocess.run(
                [
                    sys.executable,
                    str(INSTALLER),
                    "--plugin-dir",
                    str(plugin_dir),
                    "--marketplace",
                    str(marketplace),
                    "--user-skills-dir",
                    str(user_skills),
                    "--codex-config",
                    str(codex_config),
                    "--codex-hooks",
                    str(codex_hooks),
                    "--backup-root",
                    str(backup_root),
                    "--no-personal-skills",
                ],
                check=True,
            )

            manifest = json.loads((backup_root / "manifest.json").read_text(encoding="utf-8"))
            originals = {Path(entry["original"]).name for entry in manifest["entries"]}
            self.assertIn("marketplace.json", originals)
            self.assertIn("config.toml", originals)
            self.assertIn("hooks.json", originals)
            self.assertIn("codex-ralph-loop", plugin_dir.name)
            self.assertIn("codex_hooks = true", codex_config.read_text(encoding="utf-8"))

    def test_plugin_bundle_includes_documented_global_commands(self) -> None:
        expected = {
            "init-codex-ralph.md",
            "run-codex-ralph.md",
            "ralph-loop.md",
            "cancel-ralph.md",
            "summit-preflight.md",
            "summit-review-pdf.md",
            "summit-context-refresh.md",
            "summit-brainstorm.md",
            "summit-write-plan.md",
        }
        actual = {path.name for path in PLUGIN_COMMANDS_DIR.glob("*.md")}
        self.assertTrue(expected.issubset(actual))

    def test_context_engine_recent_progress_is_empty_without_iterations(self) -> None:
        mod = load_module(CONTEXT_ENGINE, "context_engine_test")
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "LOG.md"
            log_path.write_text("# Loop Log\n\nRun history will accumulate here.\n", encoding="utf-8")
            self.assertEqual(mod.recent_log_blocks(log_path), [])

    def test_first_nonempty_line_skips_promise_only_output(self) -> None:
        mod = load_module(CODEX_RALPH, "codex_ralph_first_line_test")
        text = "<promise>COMPLETE</promise>\n\nReal progress after the promise.\n"
        self.assertEqual(mod.first_nonempty_line(text), "Real progress after the promise.")
        self.assertEqual(mod.first_nonempty_line("<promise>COMPLETE</promise>\n"), "Completion promise emitted.")

    def test_context_engine_next_best_step_accepts_pending_tasks(self) -> None:
        mod = load_module(CONTEXT_ENGINE, "context_engine_pending_next_step_test")
        tasks_index = {"source": "project-specific-bootstrap"}
        tasks = [{"id": "005", "title": "Run explicit local self-smoke and reconcile handoff", "status": "pending", "priority": "p1"}]
        specs = {"005": {"dependsOn": ["004"]}}
        next_step = mod.next_best_step(tasks_index, tasks, specs, blockers=[])
        self.assertEqual(next_step, "Check whether task 005 is now unblocked by 004.")

    def test_context_engine_next_best_step_reports_completion_when_goal_eval_passed(self) -> None:
        mod = load_module(CONTEXT_ENGINE, "context_engine_complete_next_step_test")
        tasks_index = {"source": "manual"}
        tasks = [{"id": "007", "title": "Refresh final proof", "status": "done", "priority": "p0"}]
        specs = {"007": {"dependsOn": []}}
        latest_state = {"evalPassed": True, "evalStatus": "COMPLETE"}
        next_step = mod.next_best_step(tasks_index, tasks, specs, blockers=[], latest_state=latest_state)
        self.assertEqual(
            next_step,
            "Goal is complete. Archive this package or branch a derivative deliverable such as a submission-form short version or 발표용 one-pager.",
        )

    def test_context_engine_recent_progress_prefers_summary_line(self) -> None:
        mod = load_module(CONTEXT_ENGINE, "context_engine_recent_summary_test")
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            (state_dir / "logs").mkdir(parents=True, exist_ok=True)
            (state_dir / "logs" / "LOG.md").write_text(
                "# Loop Log\n\n"
                "## Iteration 0 - 2026-04-13T01:45:37+09:00\n"
                "- Task: none\n"
                "- Promise: seeded\n"
                "- Checks: Not run.\n"
                "- Review: Not run.\n"
                "- Goal Eval: Not run.\n"
                "- Summary: Task graph bootstrap completed.\n",
                encoding="utf-8",
            )
            self.assertEqual(
                mod.summarize_recent_progress(state_dir),
                ["- Iteration 0 - 2026-04-13T01:45:37+09:00: Task graph bootstrap completed."],
            )

    def test_context_engine_recent_progress_sanitizes_promise_only_summary(self) -> None:
        mod = load_module(CONTEXT_ENGINE, "context_engine_promise_summary_test")
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            (state_dir / "logs").mkdir(parents=True, exist_ok=True)
            (state_dir / "logs" / "LOG.md").write_text(
                "# Loop Log\n\n"
                "## Iteration 1 - 2026-04-13T02:23:36+09:00\n"
                "- Task: 004 Tighten operator docs and local verification\n"
                "- Promise: COMPLETE\n"
                "- Checks: All local checks passed.\n"
                "- Review: Skipped.\n"
                "- Goal Eval: Not run.\n"
                "- Summary: <promise>COMPLETE</promise>\n",
                encoding="utf-8",
            )
            self.assertEqual(
                mod.summarize_recent_progress(state_dir),
                ["- Iteration 1 - 2026-04-13T02:23:36+09:00: Completion promise emitted."],
            )

    def test_context_engine_strips_summary_heading_when_embedding(self) -> None:
        mod = load_module(CONTEXT_ENGINE, "context_engine_summary_heading_test")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state_dir = root / ".codex-loop"
            (state_dir / "prd").mkdir(parents=True, exist_ok=True)
            (state_dir / "prd" / "SUMMARY.md").write_text(
                "# Project Summary\n\nThis is the embedded summary body.\n",
                encoding="utf-8",
            )
            (state_dir / "PROMPT.md").write_text("Stable prompt body.", encoding="utf-8")

            current_state, _, _ = mod.build_context_markdown(root, state_dir)

            self.assertIn("## Project Summary\nThis is the embedded summary body.", current_state)
            self.assertNotIn("## Project Summary\n# Project Summary", current_state)

    def test_seed_prompt_calls_out_bootstrap_scaffold_files(self) -> None:
        mod = load_module(CODEX_RALPH, "codex_ralph_seed_prompt_test")
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            (state_dir / "prd").mkdir(parents=True, exist_ok=True)
            (state_dir / "PROMPT.md").write_text("Base prompt", encoding="utf-8")
            (state_dir / "prd" / "PRD.md").write_text("PRD body", encoding="utf-8")
            (state_dir / "prd" / "SUMMARY.md").write_text("Summary body", encoding="utf-8")
            (state_dir / "context").mkdir(parents=True, exist_ok=True)
            (state_dir / "context" / "handoff.md").write_text("handoff", encoding="utf-8")

            prompt = mod.build_task_seed_prompt(
                config={"loop": {"mode": "planning", "completion_promise": "COMPLETE"}},
                state_dir=state_dir,
                steering_text="",
                git_available=True,
            )

            self.assertIn(".gitignore", prompt)
            self.assertIn(".codex-loop/", prompt)
            self.assertIn("expected setup, not unrelated drift", prompt)
            self.assertIn("Prefer high-signal files like the PRD, summary, README, docs, and tests", prompt)


if __name__ == "__main__":
    unittest.main(verbosity=2)
