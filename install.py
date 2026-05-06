#!/usr/bin/env python3

from __future__ import annotations

import runpy
import sys
from pathlib import Path


def main() -> int:
    script = Path(__file__).resolve().parent / "plugins" / "codex-ralph-loop" / "scripts" / "install_home_local.py"
    if not script.exists():
        print(f"missing installer: {script}", file=sys.stderr)
        return 2

    sys.argv = [str(script), *sys.argv[1:]]
    runpy.run_path(str(script), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
