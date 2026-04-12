from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = REPO_ROOT / "plugins" / "codex-ralph-loop" / "scripts" / "bootstrap_project.py"
STOP_DISPATCH = REPO_ROOT / "plugins" / "codex-ralph-loop" / "scripts" / "stop_hook_dispatch.py"
CODEX_RALPH = REPO_ROOT / "plugins" / "codex-ralph-loop" / "templates" / "project" / "scripts" / "codex_ralph.py"
CONTEXT_ENGINE = REPO_ROOT / "plugins" / "codex-ralph-loop" / "templates" / "project" / "scripts" / "context_engine.py"
INSTALLER = REPO_ROOT / "plugins" / "codex-ralph-loop" / "scripts" / "install_home_local.py"


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
            root = Path(tmp)
            (root / ".codex").mkdir(parents=True, exist_ok=True)
            marker = root / ".codex" / "existing.txt"
            marker.write_text("keep", encoding="utf-8")
            subprocess.run([sys.executable, str(BOOTSTRAP), "--force", str(root)], check=True)
            self.assertTrue(marker.exists())
            self.assertTrue((root / "scripts" / "context_engine.py").exists())
            self.assertTrue((root / ".codex-loop" / "context" / "durable.json").exists())

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

    def test_context_engine_recent_progress_is_empty_without_iterations(self) -> None:
        mod = load_module(CONTEXT_ENGINE, "context_engine_test")
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "LOG.md"
            log_path.write_text("# Loop Log\n\nRun history will accumulate here.\n", encoding="utf-8")
            self.assertEqual(mod.recent_log_blocks(log_path), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
