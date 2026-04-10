# /run-codex-ralph

Run the project-local Codex Ralph loop.

## Recommended flow

1. Confirm that `.codex-loop/prd/PRD.md` and `.codex-loop/tasks.json` are up to date
2. Confirm that `.codex-loop/config.json` contains real local checks
3. Run `./ralph.sh -n 6` for a short supervised session
4. Use `.codex-loop/STEERING.md` for urgent course corrections during the run
5. Review `.codex-loop/logs/LOG.md`, `history/`, and `reviews/` after the session

## Stop conditions

- `COMPLETE`: open tasks, checks, and review gate all pass
- `BLOCKED:reason`: human help is required
- `DECIDE:question`: a real product decision is needed

## Notes

- This command is the external worker-style loop.
- For same-session Stop-hook Ralph, use `/ralph-loop ...` instead.
