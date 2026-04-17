---
description: Start a Stop-hook Ralph loop in the current project. Usage: /ralph-loop "<task>" --completion-promise "<promise>COMPLETE</promise>" [--max-iterations <n>]
---

# /ralph-loop

Start the hook-native Ralph loop in the current repository.

## Arguments

- The task prompt is required.
- `--completion-promise "<text>"` is optional. Default: `<promise>COMPLETE</promise>`
- `--max-iterations <n>` is optional. Default: until-complete. Use it only as an explicit safety cap.

## Workflow

1. Parse `$ARGUMENTS`.
2. If `scripts/ralph_session.py` is missing, initialize this repository with `/init-codex-ralph` first.
3. Run `python3 scripts/ralph_session.py start ...` with the parsed task prompt, completion promise, and optional max iterations.
4. Tell the user the Stop-hook loop is armed.
5. Then immediately start working on the task prompt itself so the Stop hook can keep replaying it after every attempted exit.

## Notes

- This mode is different from `./ralph.sh`: it keeps the same conversation alive with a Stop hook instead of launching a fresh `codex exec` worker each iteration.
- The default loop is now until-complete. If you want a hard ceiling, pass `--max-iterations <n>` yourself.
- Use `/cancel-ralph` to escape the loop cleanly.
