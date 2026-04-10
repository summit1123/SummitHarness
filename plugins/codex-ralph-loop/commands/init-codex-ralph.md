# /init-codex-ralph

Initialize the current project with Codex Ralph loop runtime files.

## Workflow

1. Run `python3 ~/.codex/plugins/codex-ralph-loop/scripts/bootstrap_project.py .`
2. Open `.codex-loop/prd/PRD.md` and `.codex-loop/tasks.json`
3. Replace the sample brief and tasks with the real project
4. Add build, lint, test, or screenshot commands in `.codex-loop/config.json`
5. Run `./ralph.sh --once` or start `/ralph-loop "..." --completion-promise "<promise>COMPLETE</promise>" --max-iterations 20` to verify the loop works in this project

## Notes

- Use `--force` only when you intentionally want to replace an existing setup.
- The plugin stays reusable; the seeded `.codex-loop/` becomes project-owned state.
