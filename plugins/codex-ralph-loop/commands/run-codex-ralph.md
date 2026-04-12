# /run-codex-ralph

Run the project-local SummitHarness loop.

## Recommended flow

1. Confirm `.codex-loop/prd/PRD.md` and `.codex-loop/prd/SUMMARY.md` reflect the current goal
2. If `.codex-loop/tasks.json` is still the bootstrap template, leave it alone and let the first run auto-seed it
3. If a planning or submission PDF already exists, run `python3 scripts/review_submission_pdf.py "<path-to-pdf>"`
4. Run `python3 scripts/context_engine.py refresh --source pre-run`
5. Confirm `.codex-loop/config.json` contains real local checks
6. Run `./ralph.sh -n 6` for a short supervised session
7. Use `.codex-loop/STEERING.md` for urgent course corrections during the run
8. Review `.codex-loop/context/handoff.md`, `logs/`, `history/`, `reviews/`, `evals/`, and `artifacts/pdf-review/` after the session

## Stop conditions

- `COMPLETE`: open tasks, checks, and review gate all pass
- `BLOCKED:reason`: human help is required
- `DECIDE:question`: a real product decision is needed

## Notes

- This command is the external worker-style loop.
- If the task graph is still a bootstrap template, this run seeds a real one before implementation starts.
- The goal evaluator can reopen or extend the task graph when the plan no longer matches the real goal.
- The PDF gate is for truthful attachments, not cosmetic polishing. Fix the source or task graph when it finds drift.
- For same-session Stop-hook Ralph, use `/ralph-loop ...` instead.
