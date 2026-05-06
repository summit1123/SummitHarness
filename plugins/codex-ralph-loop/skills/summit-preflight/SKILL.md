---
name: summit-preflight
description: Use when the user wants to verify that the environment, Codex hooks, toolchain, MCP setup hints, and media tooling are ready before running the harness.
---

# Summit Preflight

Use this skill before a long run or before attempting design-heavy automation.

## Workflow

1. Run `python3 scripts/preflight.py run`.
2. Read `.codex-loop/preflight/REPORT.md`.
3. Separate blockers from warnings.
4. Fix blockers before starting autonomous implementation.
5. If design or media workflows matter, call out missing Figma, ffmpeg, or API-key prerequisites.
