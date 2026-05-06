# /summit-preflight

Run the SummitHarness environment checks for the current project.

## Workflow

1. Confirm `scripts/preflight.py` exists.
2. Run `python3 scripts/preflight.py run`.
3. Summarize blockers and warnings from `.codex-loop/preflight/REPORT.md`.
4. If blockers exist, stop and tell the user what to fix first.
