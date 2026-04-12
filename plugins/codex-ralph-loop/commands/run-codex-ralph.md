# /run-codex-ralph

Run the project-local SummitHarness loop.

## Recommended flow

1. Confirm `.codex-loop/prd/PRD.md` and `.codex-loop/tasks.json` are current
2. Run `python3 scripts/context_engine.py refresh --source pre-run`
3. Confirm `.codex-loop/config.json` contains real local checks
4. Run `./ralph.sh -n 6` for a short supervised session
5. Use `.codex-loop/STEERING.md` for urgent course corrections during the run
6. Review `.codex-loop/context/handoff.md`, `logs/`, `history/`, and `reviews/` after the session

## Stop conditions

- `COMPLETE`: open tasks, checks, and review gate all pass
- `BLOCKED:reason`: human help is required
- `DECIDE:question`: a real product decision is needed

## Notes

- This command is the external worker-style loop.
- For same-session Stop-hook Ralph, use `/ralph-loop ...` instead.
