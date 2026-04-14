---
name: ralph-prd
description: Turn rough requirements or planning documents into a buildable PRD, project summary, and concrete task graph for the Codex Ralph loop.
metadata:
  priority: 5
  pathPatterns:
    - '.codex-loop/prd/**'
    - '.codex-loop/tasks.json'
    - '.codex-loop/tasks/TASK-*.json'
  promptSignals:
    phrases:
      - "write the prd"
      - "make a task list"
      - "turn this planning doc into tasks"
      - "requirements into prd"
    anyOf:
      - "hwpx"
      - "requirements"
      - "planning document"
      - "spec"
      - "brief"
    noneOf: []
    minScore: 6
retrieval:
  aliases:
    - product requirements document
    - task breakdown
    - project brief
    - acceptance criteria
  intents:
    - turn a planning document into a buildable PRD
    - break a feature into concrete tasks for the loop
    - rewrite vague requirements into implementable scope
  entities:
    - PRD.md
    - SUMMARY.md
    - tasks.json
    - TASK-001.json
  examples:
    - make a prd from this spec
    - split this feature into tasks
    - rewrite the brief so the loop can execute it
chainTo:
  -
    pattern: '(ui|ux|design|wireframe|layout|screen|flow)'
    targetSkill: ralph-design-gate
    message: 'UI and UX concerns detected in the planning brief — loading design gate guidance for flow and visual direction.'
  -
    pattern: '(proposal|submission|contest|document|markdown|attachment|pdf)'
    targetSkill: summit-document-gate
    message: 'Submission artifact concerns detected in the planning brief — loading the source-first document gate.'
  -
    pattern: '(implement|build|ship|prototype|frontend|backend|api)'
    targetSkill: ralph-runtime
    message: 'Implementation intent detected in the planning brief — loading runtime loop guidance.'
---

# Ralph PRD

This skill is for the planning phase of the loop.

## Goal

Transform raw requirements into:

- a trustworthy PRD
- a concise summary that can be sent every iteration
- a task graph with explicit acceptance criteria

## Rules

- Reduce ambiguity instead of preserving it.
- Record assumptions instead of hiding them.
- Prefer vertical slices over giant phase buckets.
- Keep one task actively executable at a time.
- If a planning or submission document already exists, run the document gate before calling the plan ready.
