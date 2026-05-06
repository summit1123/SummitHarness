---
name: ralph-brainstorm
description: Refine a rough goal into a trustworthy build brief before task planning or implementation starts.
metadata:
  priority: 5
  pathPatterns:
    - '.codex-loop/prd/**'
    - '.codex-loop/context/**'
  promptSignals:
    phrases:
      - "brainstorm this"
      - "refine the idea"
      - "shape the brief"
      - "기획서 정리"
      - "아이디어 정리"
    anyOf:
      - "goal"
      - "idea"
      - "brief"
      - "prd"
      - "brainstorm"
      - "기획"
    noneOf: []
    minScore: 6
retrieval:
  aliases:
    - product brainstorming
    - spec shaping
    - brief refinement
  intents:
    - turn a rough idea into an implementation-ready brief
    - lock the user, problem, outcome, and constraints before planning
    - reduce ambiguity before the loop starts coding
  entities:
    - PRD.md
    - SUMMARY.md
    - durable.json
    - handoff.md
  examples:
    - brainstorm this product idea
    - turn this rough concept into a sharp brief
    - 정리 안 된 요구사항을 기획서로 다듬어줘
chainTo:
  -
    pattern: '(task|plan|breakdown|execute|implementation|implement)'
    targetSkill: ralph-prd
    message: 'Planning intent detected after brainstorming — loading PRD and task graph guidance.'
---

# Ralph Brainstorm

Use this skill before planning or coding when the goal is still fuzzy.

## Goal

Turn a rough request into a brief that the loop can trust.

## Output bar

- The brief names the user, problem, desired outcome, and success bar.
- Constraints, assumptions, and open questions are visible.
- The design direction is concrete enough to avoid generic AI-looking output when UI matters.
- The result is ready to hand off to `ralph-prd` for task graph generation.

## Rules

- Reduce ambiguity instead of preserving it.
- Ask the smallest number of questions needed for trustworthy planning.
- Prefer concrete user journeys over vague feature buckets.
- If design matters, capture tone, density, references, and failure states early.
- Do not jump into implementation from this skill.
