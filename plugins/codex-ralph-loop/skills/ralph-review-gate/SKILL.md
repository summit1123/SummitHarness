---
name: ralph-review-gate
description: Add or refine a code and regression review gate for the Codex Ralph loop, focused on correctness, risks, and missing coverage.
metadata:
  priority: 4
  pathPatterns:
    - '.codex-loop/reviews/**'
    - '.codex-loop/config.json'
    - '.codex-loop/tasks/TASK-*.json'
  promptSignals:
    phrases:
      - "review gate"
      - "code review"
      - "regression check"
      - "severe only review"
    anyOf:
      - "bug"
      - "risk"
      - "tests"
      - "regression"
      - "edge case"
    noneOf: []
    minScore: 6
retrieval:
  aliases:
    - review pass
    - regression gate
    - code review evaluator
    - missing test detection
  intents:
    - add a serious review pass before the loop declares completion
    - keep the loop from exiting on green tests alone
    - review changes for correctness and missing coverage
  entities:
    - RESULT: PASS
    - RESULT: FAIL
    - findings
    - review_command
  examples:
    - add a review gate after tests pass
    - make the loop fail on material review findings
    - keep style nits out of the loop
---

# Ralph Review Gate

This skill makes the loop behave more like a real engineering team:

- implementation
- verification
- review
- only then completion

## Review posture

- findings first
- severe-only
- correctness over style
- missing tests matter when behavior changed
