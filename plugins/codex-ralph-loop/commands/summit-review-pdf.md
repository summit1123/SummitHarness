# /summit-review-pdf

Review a planning or submission PDF before the next Ralph pass.

## Workflow

1. Pick the PDF you want to verify.
2. Run `python3 scripts/review_submission_pdf.py "<path-to-pdf>"`.
3. Read the generated report in `.codex-loop/artifacts/pdf-review/`.
4. Compare the extracted preview against `.codex-loop/prd/PRD.md`, `.codex-loop/prd/SUMMARY.md`, and the actual submission form fields.
5. If the PDF and the plan disagree, fix the source document or task graph first.
6. Run `python3 scripts/context_engine.py refresh --source pdf-review`.
7. Then start `./ralph.sh -n 6` or `/ralph-loop ...` for the next supervised pass.

## Notes

- This gate is especially useful for contest submissions and other attachment-driven work.
- The checker enforces a `.pdf` extension, a default `20MB` upload limit, and a filename without commas.
