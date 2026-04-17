---
description: Start SummitHarness onboarding, choose the right workflow profile, and prepare the project for the correct Ralph path.
---

# /ralph-start

Use this as the first command after installing the plugin or entering a new project.

## Workflow

1. Inspect the current repo, attachments, PDFs, PRDs, or user prompt before doing anything else.
2. If the current repo already looks like the SummitHarness source itself, or a plugin source repo that contains `plugins/codex-ralph-loop/`, do **not** bootstrap it in place by default. First ask whether the user wants to:
   - improve the harness itself, or
   - use the harness in a separate target project
3. If `scripts/summit_start.py` is missing and the current repo is a normal target project, initialize the repository with `/init-codex-ralph` first.
4. Ask a structured onboarding Q&A with enough depth to decide:
   - whether this is `proposal-only`, `planning-only`, `build-direct`, or `idea-to-service`
   - what the honest final deliverable is
   - whether idea exploration is still needed
   - whether design, frontend, backend, AI modules, or submission packaging are in scope
   - what research depth, references, or evidence gathering are required first
   - who approves the direction and what evidence must exist before COMPLETE is honest
5. If the answers are not already explicit in the prompt or attached materials, stop after the current onboarding pass and wait for the user response. Continue the onboarding in additional passes until the workflow profile, goal sentence, scope, and evidence bar are genuinely locked. Do **not** choose `build-direct`, `idea-to-service`, or any other profile by guess.
6. Do not run `python3 scripts/summit_start.py init ...` in the same turn unless the workflow profile, goal sentence, scope, approval path, and evidence bar are already explicit or the user has just confirmed them.
7. After the profile and goal are explicit, run `python3 scripts/summit_start.py init --profile <chosen-profile> --goal "<locked goal sentence>"`.
8. Capture the real answers in `.codex-loop/workflow/ONBOARDING.md` and, if needed, compare options in `.codex-loop/workflow/IDEAS.md`.
9. Then initialize or refresh intake and research docs for the current workflow stage, refresh the context packet, and summarize the correct next stage.
10. Do not write approval docs as if they are already approved. Leave them pending until the user actually confirms the direction.
11. Do not start the autonomous Ralph loop until the user has enough clarity to approve the first stage honestly. Onboarding depth matters more than speed.

## Notes

- `workflow profile` is the top-level journey; `mode` is the lower-level operating contract for the current stage.
- `idea-to-service` is the default only when the user explicitly wants idea exploration through product build in one harness.
