# /summit-review-doc

Review the Markdown document source before rendering or final submission.

1. Identify the real source document, usually `docs/submissions/proposal.md`.
2. Run `python3 scripts/review_submission_source.py docs/submissions/proposal.md`.
3. Read the generated report in `.codex-loop/artifacts/source-review/`.
4. Fix the source, not only the layout.
5. Refresh context with `python3 scripts/context_engine.py refresh --source source-review`.
