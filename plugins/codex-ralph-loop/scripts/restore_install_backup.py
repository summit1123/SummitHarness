#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


def load_manifest(backup_root: Path) -> dict:
    manifest_path = backup_root / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"missing manifest: {manifest_path}")
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def restore_entry(entry: dict) -> None:
    original = Path(entry["original"]).expanduser().resolve()
    backup = Path(entry["backup"]).expanduser().resolve()
    kind = entry.get("type", "file")

    if original.exists() or original.is_symlink():
        if original.is_dir() and not original.is_symlink():
            shutil.rmtree(original)
        else:
            original.unlink()

    if kind == "directory":
        shutil.copytree(backup, original)
    else:
        original.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(backup, original)


def main() -> int:
    parser = argparse.ArgumentParser(description="Restore a SummitHarness install backup.")
    parser.add_argument("backup_root", help="Backup directory that contains manifest.json")
    args = parser.parse_args()

    backup_root = Path(args.backup_root).expanduser().resolve()
    manifest = load_manifest(backup_root)
    entries = manifest.get("entries", [])
    for entry in entries:
        restore_entry(entry)
        print(f"Restored {entry['original']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
