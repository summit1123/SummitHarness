# .codex-loop

This directory is the runtime state for the loop.

- `prd/`: the product brief the loop must respect
- `tasks.json`: lookup table for task priority and status
- `tasks/TASK-*.json`: one task spec per unit of work
- `PROMPT.md`: the stable instruction block sent every iteration
- `STEERING.md`: urgent manual course corrections
- `logs/`, `history/`, `reviews/`: run records

The plugin is reusable. This directory is where the project becomes yours.
