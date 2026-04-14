---
name: summit-document-gate
description: Review Markdown proposal or document source before rendering, then feed the findings back into the PRD, context packet, and next Ralph pass.
metadata:
  priority: 4
  pathPatterns:
    - '.codex-loop/artifacts/source-review/**'
    - 'docs/submissions/**'
    - '.codex-loop/design/DESIGN.md'
    - 'scripts/review_submission_source.py'
    - 'scripts/render_markdown_submission.py'
  promptSignals:
    phrases:
      - "review the proposal source"
      - "check the markdown document"
      - "submission markdown"
      - "document gate"
    anyOf:
      - "proposal"
      - "submission"
      - "markdown"
      - "document"
      - "contest"
    noneOf: []
    minScore: 5
retrieval:
  aliases:
    - source gate
    - markdown proposal review
    - document readiness review
  intents:
    - check whether the Markdown source is strong enough before rendering or submission
    - compare the source draft against the PRD and submission form
    - turn document review findings into concrete follow-up tasks
  entities:
    - review_submission_source.py
    - render_markdown_submission.py
    - proposal.md
    - DESIGN.md
  examples:
    - review the proposal markdown before we render the pdf
    - check whether the document source is ready for submission
chainTo:
  -
    pattern: '(pdf|attachment|upload)'
    targetSkill: summit-pdf-gate
    message: 'Final attachment concerns detected — load the PDF gate after the source gate passes.'
  -
    pattern: '(prd|task|plan|requirements|brief)'
    targetSkill: ralph-prd
    message: 'Planning artifacts detected — load PRD guidance so source findings flow back into the task graph.'
---

# Summit Document Gate

Use this when a proposal, contest submission, or reviewer-facing document needs a hard source check before the loop continues.

## Workflow

1. Run `python3 scripts/review_submission_source.py docs/submissions/proposal.md` or the relevant Markdown source path.
2. Read the generated markdown and json in `.codex-loop/artifacts/source-review/`.
3. Fix the source itself, not just the final layout.
4. Render with `python3 scripts/render_markdown_submission.py` after the source gate passes.
5. Refresh the context packet with `python3 scripts/context_engine.py refresh --source source-review`.
6. Only then run `./ralph.sh` or `/ralph-loop ...`.
