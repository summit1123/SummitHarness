---
description: 승인된 Markdown 제출 원고를 HTML과 PDF 산출물로 렌더링합니다.
---

# /summit-render-doc

Render the approved Markdown source into HTML and PDF.

1. Make sure the latest source review has no blockers.
2. Run `python3 scripts/render_markdown_submission.py`.
3. Inspect `output/html/` and `output/pdf/`.
4. If needed, run `python3 scripts/review_submission_pdf.py output/pdf/proposal.pdf` as the final attachment gate.
