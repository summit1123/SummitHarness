---
name: codex-ralph-loop
description: Run a project-local Codex Ralph loop that works from PRD, task files, steering notes, local checks, and a read-only review gate.
---

# Codex Ralph Loop

Use this when the user wants a long-running build loop rather than a one-off
implementation pass.

## Working shape

1. Keep the project state in `/.codex-loop/`.
2. Make the PRD and task files concrete before running the loop.
3. Put deterministic commands in `.codex-loop/config.json` under `checks.commands`.
4. Run `./ralph.sh` from the repo root.
5. Treat `.codex-loop/STEERING.md` as an interrupt lane for urgent notes.

## Promise tags

- `<promise>COMPLETE</promise>`
- `<promise>BLOCKED:reason</promise>`
- `<promise>DECIDE:question</promise>`

Never emit `COMPLETE` unless the open tasks are actually done and the loop gates
can pass.

## Practical guidance

- Make task files specific enough that the agent can act without guessing.
- Keep review severe-only so the loop can converge.
- Prefer one active task at a time.
- Add real build, lint, test, or screenshot checks as soon as the project has
  them.
