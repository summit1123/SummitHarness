# /run-codex-ralph

Run the project-local SummitHarness loop.

## Recommended flow

1. Confirm `.codex-loop/prd/PRD.md` and `.codex-loop/prd/SUMMARY.md` reflect the current goal
2. If `.codex-loop/tasks.json` is still the bootstrap template, leave it alone and let the first run auto-seed it
3. Run `python3 scripts/context_engine.py refresh --source pre-run`
4. Confirm `.codex-loop/config.json` contains real local checks
5. Run `./ralph.sh -n 6` for a short supervised session
6. Use `.codex-loop/STEERING.md` for urgent course corrections during the run
7. Review `.codex-loop/context/handoff.md`, `logs/`, `history/`, `reviews/`, and `evals/` after the session

## Stop conditions

- `COMPLETE`: open tasks, checks, and review gate all pass
- `BLOCKED:reason`: human help is required
- `DECIDE:question`: a real product decision is needed

## Notes

- This command is the external worker-style loop.
- If the task graph is still a bootstrap template, this run seeds a real one before implementation starts.
- The goal evaluator can reopen or extend the task graph when the plan no longer matches the real goal.
- For same-session Stop-hook Ralph, use `/ralph-loop ...` instead.
