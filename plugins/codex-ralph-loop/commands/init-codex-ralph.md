# /init-codex-ralph

Initialize the current project with SummitHarness runtime files.

## Workflow

1. Run `python3 ~/.codex/plugins/codex-ralph-loop/scripts/bootstrap_project.py .`
2. Run `python3 scripts/preflight.py run`
3. Run `python3 scripts/context_engine.py refresh --source bootstrap`
4. Open `.codex-loop/prd/PRD.md` and `.codex-loop/prd/SUMMARY.md` and write the real goal
5. Add real build, lint, test, or screenshot commands in `.codex-loop/config.json`
6. Run `./ralph.sh --once` or start `/ralph-loop ...`
7. The first Ralph run will replace the bootstrap template tasks with a project-specific task graph before continuing

## Notes

- Use `--force` only when you intentionally want to replace existing runtime files.
- The plugin stays reusable; the seeded `.codex-loop/` becomes project-owned state.
