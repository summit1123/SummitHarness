---
description: Start SummitHarness onboarding, choose the right workflow profile, and prepare the project for the correct Ralph path.
---

# /ralph-start

Use this as the first command after installing the plugin or entering a new project.

## Workflow

1. If `scripts/summit_start.py` is missing, initialize the repository with `/init-codex-ralph` first.
2. Inspect the current repo, attachments, PDFs, PRDs, or user prompt to understand what kind of run this is.
3. Ask a short onboarding Q&A that decides:
   - whether this is `proposal-only`, `planning-only`, `build-direct`, or `idea-to-service`
   - what the honest final deliverable is
   - whether idea exploration is still needed
   - whether design, frontend, backend, AI modules, or submission packaging are in scope
   - what evidence must exist before COMPLETE is honest
4. Run `python3 scripts/summit_start.py init --profile <chosen-profile> --goal "<locked goal sentence>"`.
5. Capture the real answers in `.codex-loop/workflow/ONBOARDING.md` and, if needed, compare options in `.codex-loop/workflow/IDEAS.md`.
6. Then initialize or refresh intake and research docs for the current workflow stage, refresh the context packet, and summarize the correct next stage.
7. Do not start the autonomous Ralph loop until the user has enough clarity to approve the first stage honestly.

## Notes

- `workflow profile` is the top-level journey; `mode` is the lower-level operating contract for the current stage.
- `idea-to-service` is the default when the user wants idea exploration through product build in one harness.
