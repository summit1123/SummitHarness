---
name: ralph-design-gate
description: 제품이 기계적으로 보이지 않도록 Ralph 루프에 디자인과 UX 검수 기준을 적용합니다.
metadata:
  priority: 4
  pathPatterns:
    - '.codex-loop/prd/**'
    - '.codex-loop/tasks/TASK-*.json'
  promptSignals:
    phrases:
      - "design gate"
      - "ui review"
      - "ux review"
      - "make it feel designed"
      - "not ai-looking"
    anyOf:
      - "screenshot"
      - "mobile"
      - "desktop"
      - "flow"
      - "layout"
      - "copy"
    noneOf: []
    minScore: 6
retrieval:
  aliases:
    - design review
    - ux gate
    - screenshot check
    - visual direction
  intents:
    - define the product flow and visual direction before implementation sprawls
    - review a UI for realism and polish instead of generic AI style
    - add screenshot-based or flow-based design checks to the loop
  entities:
    - user flow
    - design direction
    - loading state
    - empty state
    - error state
  examples:
    - add a design gate to the loop
    - review this ui so it feels intentional
    - define the ux flow before building
---

# Ralph Design Gate

This skill keeps the loop from shipping technically correct but emotionally dead
UI.

## Gate bar

- Primary user flow is explicit.
- Empty, loading, success, and error states are considered.
- Layout, hierarchy, and copy direction are written down before polishing.
- Screenshot or viewport checks are added when the project has a UI.
