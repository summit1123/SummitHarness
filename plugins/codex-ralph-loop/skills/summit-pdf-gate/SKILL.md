---
name: summit-pdf-gate
description: Review a planning or submission PDF for upload constraints and feed the findings back into the PRD, context packet, and next Ralph pass.
metadata:
  priority: 4
  pathPatterns:
    - '.codex-loop/artifacts/pdf-review/**'
    - '.codex-loop/prd/**'
    - '.codex-loop/tasks.json'
    - 'scripts/review_submission_pdf.py'
  promptSignals:
    phrases:
      - "review the pdf"
      - "check the proposal pdf"
      - "submission pdf"
      - "attachment review"
    anyOf:
      - "pdf"
      - "proposal"
      - "contest"
      - "submission"
      - "attachment"
    noneOf: []
    minScore: 5
retrieval:
  aliases:
    - submission gate
    - proposal attachment review
    - planning pdf check
  intents:
    - check a generated pdf before submission or before the next loop run
    - compare the attachment draft against the prd and form fields
    - turn pdf review findings into concrete follow-up tasks
  entities:
    - review_submission_pdf.py
    - PRD.md
    - SUMMARY.md
    - tasks.json
  examples:
    - review the proposal pdf before we submit it
    - check whether the attachment is ready for upload
chainTo:
  -
    pattern: '(prd|task|plan|requirements|brief)'
    targetSkill: ralph-prd
    message: 'Planning artifacts detected — loading PRD guidance so the PDF findings can flow back into the task graph.'
  -
    pattern: '(implement|build|prototype|develop|ralph|loop)'
    targetSkill: ralph-runtime
    message: 'Loop follow-up detected — loading runtime guidance for the next Ralph pass.'
---

# Summit PDF Gate

Use this when a planning PDF, contest attachment, or final proposal draft needs one more hard check before the loop continues.

## Workflow

1. Run `python3 scripts/review_submission_pdf.py "<path-to-pdf>"`.
2. Read the generated markdown and json in `.codex-loop/artifacts/pdf-review/`.
3. Verify that the extracted preview matches `.codex-loop/prd/PRD.md`, `.codex-loop/prd/SUMMARY.md`, and the real submission form.
4. Turn any mismatch into a concrete change:
   - fix the document source,
   - update the PRD or summary,
   - or add a task so Ralph can resolve it truthfully.
5. Refresh the context packet with `python3 scripts/context_engine.py refresh --source pdf-review`.
6. Only then run `./ralph.sh` or `/ralph-loop ...`.

## What this gate should catch

- wrong attachment file type
- filenames with commas
- oversized PDFs
- obvious text mismatch between the PDF draft and the current plan
- "looks done" situations where the attachment still disagrees with the real goal
