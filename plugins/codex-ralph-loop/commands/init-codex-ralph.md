# /init-codex-ralph

Initialize the current project with SummitHarness runtime files.

## Workflow

1. Run `python3 ~/.codex/plugins/codex-ralph-loop/scripts/bootstrap_project.py .`
2. Run `python3 scripts/preflight.py run`
3. Run `python3 scripts/summit_start.py init --profile <proposal-only|planning-only|build-direct|idea-to-service> --goal "<goal>"`
4. Fill `.codex-loop/workflow/ONBOARDING.md` and, if needed, `.codex-loop/workflow/IDEAS.md`
5. Run `python3 scripts/summit_intake.py init --mode <proposal|prd|implementation|product-ui>`
6. Capture the requester Q&A in `.codex-loop/intake/ANSWERS.md` and lock approval in `.codex-loop/intake/APPROVAL.md`
7. Run `python3 scripts/summit_research.py init --mode <proposal|prd|implementation|product-ui>`
8. Write the staged research plan and lock `.codex-loop/research/APPROVAL.md`
9. Open `.codex-loop/prd/PRD.md` and `.codex-loop/prd/SUMMARY.md` and rewrite them against the approved goal and research direction
10. If a planning or submission PDF already exists, run `python3 scripts/review_submission_pdf.py "<path-to-pdf>"`
11. Run `python3 scripts/context_engine.py refresh --source bootstrap`
12. Add real build, lint, test, or screenshot commands in `.codex-loop/config.json`
13. Run `./ralph.sh` or start `/ralph-loop ...`. Use `--once` only for smoke/debug runs
14. The first Ralph run will replace the bootstrap template tasks with a project-specific task graph after workflow, intake, and research are all aligned

## Notes

- Use `--force` only when you intentionally want to replace existing runtime files.
- The plugin stays reusable; the seeded `.codex-loop/` becomes project-owned state.
- If the current repo is the SummitHarness source/plugin repo itself, do not run this in place unless the user explicitly wants to modify the harness inside that repo.
