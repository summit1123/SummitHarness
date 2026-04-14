# /summit-review-pdf

Review the final rendered PDF attachment after the Markdown source already passed.

1. Confirm the source review is already clean.
2. Run `python3 scripts/review_submission_pdf.py "output/pdf/proposal.pdf"` or the final attachment path.
3. Read the generated report in `.codex-loop/artifacts/pdf-review/`.
4. Fix filename, size, or packaging issues.
5. Refresh context with `python3 scripts/context_engine.py refresh --source pdf-review`.
