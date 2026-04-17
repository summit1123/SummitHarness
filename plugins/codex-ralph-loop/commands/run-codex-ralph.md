# /run-codex-ralph

Run the project-local SummitHarness loop.

## Recommended flow

1. Confirm `.codex-loop/intake/APPROVAL.md` is genuinely approved for the current goal
2. Confirm `.codex-loop/research/APPROVAL.md` is genuinely approved for the current direction and staged plan
3. Confirm `.codex-loop/prd/PRD.md` and `.codex-loop/prd/SUMMARY.md` reflect the approved goal
4. If `.codex-loop/tasks.json` is still the bootstrap template, leave it alone and let the first run auto-seed it
5. If a planning or submission PDF already exists, run `python3 scripts/review_submission_pdf.py "<path-to-pdf>"`
6. Run `python3 scripts/context_engine.py refresh --source pre-run`
7. Confirm `.codex-loop/config.json` contains real local checks
8. Run `./ralph.sh -n 6` for a short supervised session
9. Use `.codex-loop/STEERING.md` for urgent course corrections during the run
10. Review `.codex-loop/context/handoff.md`, `logs/`, `history/`, `reviews/`, `evals/`, and `artifacts/pdf-review/` after the session

## Stop conditions

- `COMPLETE`: open tasks, checks, and review gate all pass
- `BLOCKED:reason`: human help is required
- `DECIDE:question`: a real product decision is needed

## Notes

- This command is the external worker-style loop.
- If the intake approval is still pending, the loop should stop and ask for clarification instead of seeding tasks.
- If the research plan approval is still pending, the loop should stop and ask for staged planning instead of seeding tasks.
- If the task graph is still a bootstrap template, this run seeds a real one only after intake and research approval.
- The goal evaluator can reopen or extend the task graph when the plan no longer matches the real goal.
- The PDF gate is for truthful attachments, not cosmetic polishing. Fix the source or task graph when it finds drift.
- For same-session Stop-hook Ralph, use `/ralph-loop ...` instead.
