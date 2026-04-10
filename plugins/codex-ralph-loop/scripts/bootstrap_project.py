#!/usr/bin/env python3

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store")

GITIGNORE_BLOCK = """# Codex Ralph loop
.codex-loop/history/*
!.codex-loop/history/.gitkeep
.codex-loop/reviews/*
!.codex-loop/reviews/.gitkeep
.codex-loop/artifacts/*
!.codex-loop/artifacts/.gitkeep
.codex-loop/state.json
.codex-loop/logs/iteration-*.log
"""


def copy_tree(src: Path, dst: Path, force: bool) -> None:
    if dst.exists():
        if not force:
            raise FileExistsError(f"refusing to overwrite existing path: {dst}")
        if dst.is_dir():
            shutil.rmtree(dst)
        else:
            dst.unlink()
    shutil.copytree(src, dst, ignore=IGNORE)


def copy_file(src: Path, dst: Path, force: bool) -> None:
    if dst.exists() and not force:
        raise FileExistsError(f"refusing to overwrite existing file: {dst}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Seed a project with Codex Ralph loop runtime files."
    )
    parser.add_argument(
        "target",
        nargs="?",
        default=".",
        help="Project directory to initialize",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing runtime files",
    )
    args = parser.parse_args()

    plugin_root = Path(__file__).resolve().parents[1]
    template_root = plugin_root / "templates" / "project"
    target_root = Path(args.target).expanduser().resolve()

    if not template_root.exists():
        print(f"missing template directory: {template_root}", file=sys.stderr)
        return 2

    target_root.mkdir(parents=True, exist_ok=True)

    copy_tree(template_root / ".codex-loop", target_root / ".codex-loop", args.force)
    copy_file(
        template_root / "scripts" / "codex_ralph.py",
        target_root / "scripts" / "codex_ralph.py",
        args.force,
    )
    copy_file(
        template_root / "scripts" / "import_hwpx_preview.py",
        target_root / "scripts" / "import_hwpx_preview.py",
        args.force,
    )
    copy_file(template_root / "ralph.sh", target_root / "ralph.sh", args.force)

    ralph_path = target_root / "ralph.sh"
    ralph_path.chmod(0o755)
    (target_root / "scripts" / "codex_ralph.py").chmod(0o755)
    (target_root / "scripts" / "import_hwpx_preview.py").chmod(0o755)

    gitignore_path = target_root / ".gitignore"
    existing = gitignore_path.read_text(encoding="utf-8") if gitignore_path.exists() else ""
    if "# Codex Ralph loop" not in existing:
        gitignore_path.write_text(
            (existing.rstrip() + "\n\n" if existing.strip() else "") + GITIGNORE_BLOCK + "\n",
            encoding="utf-8",
        )

    print(f"Initialized Codex Ralph loop in {target_root}")
    print("Next steps:")
    print("  1. Edit .codex-loop/prd/PRD.md and SUMMARY.md")
    print("  2. Replace the sample tasks in .codex-loop/tasks.json")
    print("  3. Add real checks in .codex-loop/config.json")
    print("  4. Run ./ralph.sh --once")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
