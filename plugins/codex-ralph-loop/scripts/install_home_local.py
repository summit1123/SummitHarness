#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
from pathlib import Path


PLUGIN_NAME = "codex-ralph-loop"
IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store")


def read_json(path: Path, default: dict) -> dict:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def replace_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=IGNORE)


def link_or_copy_skill(src: Path, dst: Path) -> str:
    if dst.exists() or dst.is_symlink():
        if dst.is_symlink() or dst.is_file():
            dst.unlink()
        else:
            shutil.rmtree(dst)

    try:
        os.symlink(src, dst, target_is_directory=True)
        return "symlinked"
    except OSError:
        shutil.copytree(src, dst)
        return "copied"


def marketplace_source_path(install_root: Path, home: Path) -> str:
    try:
        rel = install_root.relative_to(home)
        return "./" + rel.as_posix()
    except ValueError:
        return str(install_root)


def install_plugin(plugin_root: Path, install_root: Path, marketplace_path: Path, home: Path) -> tuple[Path, Path]:
    install_root.parent.mkdir(parents=True, exist_ok=True)
    replace_tree(plugin_root, install_root)

    marketplace = read_json(
        marketplace_path,
        {
            "name": "local-home",
            "interface": {"displayName": "Local Home Plugins"},
            "plugins": [],
        },
    )
    plugins = [entry for entry in marketplace.get("plugins", []) if entry.get("name") != PLUGIN_NAME]
    plugins.append(
        {
            "name": PLUGIN_NAME,
            "source": {"source": "local", "path": marketplace_source_path(install_root, home)},
            "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
            "category": "Coding",
        }
    )
    marketplace["plugins"] = plugins
    marketplace.setdefault("name", "local-home")
    marketplace.setdefault("interface", {"displayName": "Local Home Plugins"})
    write_json(marketplace_path, marketplace)
    return install_root, marketplace_path


def ensure_codex_hooks_enabled(config_path: Path) -> None:
    if not config_path.exists():
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text("[features]\ncodex_hooks = true\n", encoding="utf-8")
        return

    text = config_path.read_text(encoding="utf-8")
    if re.search(r"(?m)^codex_hooks\s*=\s*true\s*$", text):
        return
    if re.search(r"(?m)^codex_hooks\s*=\s*false\s*$", text):
        text = re.sub(r"(?m)^codex_hooks\s*=\s*false\s*$", "codex_hooks = true", text, count=1)
        config_path.write_text(text, encoding="utf-8")
        return
    if "[features]" in text:
        text = text.replace("[features]", "[features]\ncodex_hooks = true", 1)
    else:
        if not text.endswith("\n"):
            text += "\n"
        text += "\n[features]\ncodex_hooks = true\n"
    config_path.write_text(text, encoding="utf-8")


def install_global_stop_hook(hooks_path: Path, install_root: Path) -> Path:
    hooks = read_json(hooks_path, {"hooks": {}})
    hook_map = hooks.setdefault("hooks", {})
    stop_entries = hook_map.setdefault("Stop", [])
    command = f'python3 "{(install_root / "scripts" / "stop_hook_dispatch.py").as_posix()}"'

    filtered = []
    for entry in stop_entries:
        nested = entry.get("hooks", []) if isinstance(entry, dict) else []
        keep = True
        for hook in nested:
            if isinstance(hook, dict) and hook.get("command") == command:
                keep = False
                break
        if keep:
            filtered.append(entry)

    filtered.append({"hooks": [{"type": "command", "command": command}]})
    hook_map["Stop"] = filtered
    write_json(hooks_path, hooks)
    return hooks_path


def install_personal_skills(repo_root: Path, user_skills_dir: Path) -> list[str]:
    personal_root = repo_root / "personal-skills"
    if not personal_root.exists():
        return []

    installed = []
    user_skills_dir.mkdir(parents=True, exist_ok=True)
    for skill_dir in sorted(path for path in personal_root.iterdir() if path.is_dir()):
        if not (skill_dir / "SKILL.md").exists():
            continue
        target = user_skills_dir / skill_dir.name
        mode = link_or_copy_skill(skill_dir, target)
        installed.append(f"{skill_dir.name} ({mode})")
    return installed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install the Codex Ralph loop plugin for local Codex use.")
    parser.add_argument(
        "--plugin-dir",
        default=str(Path.home() / ".codex" / "plugins" / PLUGIN_NAME),
        help="Where to install the plugin",
    )
    parser.add_argument(
        "--marketplace",
        default=str(Path.home() / ".agents" / "plugins" / "marketplace.json"),
        help="Marketplace manifest to update",
    )
    parser.add_argument(
        "--user-skills-dir",
        default=str(Path.home() / ".agents" / "skills"),
        help="Where optional personal skills should be linked",
    )
    parser.add_argument(
        "--codex-config",
        default=str(Path.home() / ".codex" / "config.toml"),
        help="Codex config.toml to patch with codex_hooks = true",
    )
    parser.add_argument(
        "--codex-hooks",
        default=str(Path.home() / ".codex" / "hooks.json"),
        help="Global hooks.json to update with the Ralph Stop hook dispatcher",
    )
    parser.add_argument(
        "--no-personal-skills",
        action="store_true",
        help="Skip installing repo-local personal skills",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    plugin_root = Path(__file__).resolve().parents[1]
    repo_root = plugin_root.parents[1]
    home = Path.home().resolve()
    install_root = Path(args.plugin_dir).expanduser().resolve()
    marketplace_path = Path(args.marketplace).expanduser().resolve()
    user_skills_dir = Path(args.user_skills_dir).expanduser().resolve()
    codex_config_path = Path(args.codex_config).expanduser().resolve()
    codex_hooks_path = Path(args.codex_hooks).expanduser().resolve()

    installed_plugin_path, installed_marketplace = install_plugin(
        plugin_root, install_root, marketplace_path, home
    )
    ensure_codex_hooks_enabled(codex_config_path)
    installed_hooks = install_global_stop_hook(codex_hooks_path, install_root)

    personal = []
    if not args.no_personal_skills:
        personal = install_personal_skills(repo_root, user_skills_dir)

    print(f"Installed plugin to {installed_plugin_path}")
    print(f"Updated marketplace at {installed_marketplace}")
    print(f"Enabled codex_hooks in {codex_config_path}")
    print(f"Installed Stop hook dispatcher in {installed_hooks}")
    if personal:
        print("Installed personal skills:")
        for skill in personal:
            print(f"  - {skill}")
    elif not args.no_personal_skills:
        print("No personal skills were found under personal-skills/.")
    print("Restart Codex if the plugin or hooks do not appear immediately.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
