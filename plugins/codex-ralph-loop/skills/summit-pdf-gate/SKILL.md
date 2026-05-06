---
name: summit-pdf-gate
description: Review a rendered PDF only as the final attachment packaging step, then feed the findings back into the context packet and next Ralph pass.
metadata:
  priority: 4
  pathPatterns:
    - '.codex-loop/artifacts/pdf-review/**'
    - 'output/pdf/**'
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
    - attachment gate
    - proposal pdf review
    - final upload check
  intents:
    - check a rendered pdf before upload or before the final loop completion call
    - verify file naming, size, and extractable attachment truth
    - turn pdf packaging findings into concrete follow-up tasks
  entities:
    - review_submission_pdf.py
    - output/pdf/proposal.pdf
  examples:
    - review the proposal pdf before we submit it
    - check whether the attachment is ready for upload
chainTo:
  -
    pattern: '(source|markdown|document)'
    targetSkill: summit-document-gate
    message: 'Source concerns detected — make sure the Markdown source passes before trusting the PDF package.'
---

# Summit PDF Gate

Use this when the final rendered PDF needs one more hard check before upload.

## Workflow

1. Run `python3 scripts/review_submission_pdf.py "output/pdf/proposal.pdf"` or the relevant attachment path.
2. Read the generated markdown and json in `.codex-loop/artifacts/pdf-review/`.
3. Fix any filename, size, or extractable-text mismatch.
4. Refresh the context packet with `python3 scripts/context_engine.py refresh --source pdf-review`.
5. Only then mark the attachment package complete.
