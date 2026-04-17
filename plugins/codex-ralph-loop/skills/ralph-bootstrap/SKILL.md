---
name: ralph-bootstrap
description: Initialize a project-local Codex Ralph loop runtime with PRD, task files, steering notes, and the loop runner entrypoint.
metadata:
  priority: 5
  pathPatterns:
    - '.codex-loop/**'
    - 'ralph.sh'
    - 'scripts/codex_ralph.py'
  bashPatterns:
    - '\bpython3\s+.*bootstrap_project\.py\b'
    - '\./ralph\.sh\b'
  promptSignals:
    phrases:
      - "set up ralph"
      - "bootstrap loop"
      - "initialize codex ralph"
      - "seed .codex-loop"
    anyOf:
      - "plugin"
      - "template"
      - "bootstrap"
      - "scaffold"
    noneOf: []
    minScore: 5
retrieval:
  aliases:
    - codex loop setup
    - project bootstrap
    - task runtime init
  intents:
    - initialize a repo for a long-running Codex loop
    - add PRD and task state files to a project
    - install the ralph loop runner into a workspace
  entities:
    - .codex-loop
    - ralph.sh
    - codex_ralph.py
    - bootstrap_project.py
  examples:
    - initialize this repo with codex ralph
    - add the loop runtime to my project
    - bootstrap .codex-loop in the current workspace
---

# Ralph Bootstrap

Use this skill when the user wants the loop scaffold to feel native to the
project rather than like a detached script.

## Workflow

1. Seed `.codex-loop/` into the target project.
2. Add `ralph.sh` and `scripts/codex_ralph.py`.
3. Make sure `.gitignore` contains loop runtime ignores.
4. Leave the project with a runnable `./ralph.sh` path, with `--once` available only as a smoke/debug variant.

## Output bar

- The project can run the loop locally.
- PRD and task files exist and are easy to edit.
- The user does not have to manually assemble the runtime from scattered files.
