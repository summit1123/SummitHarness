---
name: codex-ralph-loop
description: Run a project-local SummitHarness loop that works from PRD, tasks, compressed context, local checks, review gates, and optional Stop-hook self-loops.
---

# SummitHarness Loop

Use this when the user wants a long-running build harness rather than a one-off implementation pass.

## Working shape

1. Keep the project state in `/.codex-loop/`.
2. Refresh `.codex-loop/context/handoff.md` as repo state changes.
3. Keep the PRD, task files, and approved assets concrete before running the loop.
4. Put deterministic commands in `.codex-loop/config.json` under `checks.commands`.
5. Run `./ralph.sh` from the repo root or use `/ralph-loop ...` for same-session hook mode.
6. Treat `.codex-loop/STEERING.md` as an interrupt lane for urgent notes.

## Promise tags

- `<promise>COMPLETE</promise>`
- `<promise>BLOCKED:reason</promise>`
- `<promise>DECIDE:question</promise>`

Never emit completion unless the open tasks are actually done and the loop gates can pass.
