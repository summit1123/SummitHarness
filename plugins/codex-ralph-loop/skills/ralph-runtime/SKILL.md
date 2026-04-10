---
name: ralph-runtime
description: Run or refine the Codex Ralph loop for implementation work, using project tasks, local checks, and promise-based stop conditions.
metadata:
  priority: 5
  pathPatterns:
    - '.codex-loop/config.json'
    - '.codex-loop/logs/**'
    - '.codex-loop/history/**'
    - 'scripts/codex_ralph.py'
    - 'ralph.sh'
  bashPatterns:
    - '\./ralph\.sh\b'
    - '\bcodex\s+exec\b'
  promptSignals:
    phrases:
      - "run the loop"
      - "keep iterating"
      - "use ralph"
      - "long running codex"
    anyOf:
      - "checks"
      - "iterations"
      - "complete"
      - "blocked"
      - "decide"
    noneOf: []
    minScore: 6
retrieval:
  aliases:
    - agent loop
    - long-running codex
    - completion promise
    - evaluator loop
  intents:
    - run a task-driven Codex loop until the work is genuinely done
    - add checks and gates to an implementation loop
    - inspect why the loop stopped or failed to converge
  entities:
    - COMPLETE
    - BLOCKED
    - DECIDE
    - config.json
    - LOG.md
  examples:
    - run the codex ralph loop for 6 iterations
    - add lint and test checks to the loop
    - inspect why the loop stopped with blocked
chainTo:
  -
    pattern: '(review|regression|bug|missing test|edge case)'
    targetSkill: ralph-review-gate
    message: 'Review and regression concerns detected — loading review gate guidance.'
  -
    pattern: '(design|ux|visual|mobile|screenshot|layout)'
    targetSkill: ralph-design-gate
    message: 'Design-sensitive work detected — loading design gate guidance.'
---

# Ralph Runtime

Use this skill when the user wants the loop to actually drive implementation.

## Expectations

- The loop should read task state, not rely on memory alone.
- Deterministic commands belong in `checks.commands`.
- Promise tags are a hard contract, not an escape hatch.
- Review should stay severe-only so the loop can converge.
