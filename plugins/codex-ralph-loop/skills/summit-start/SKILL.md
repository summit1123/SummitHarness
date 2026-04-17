# Summit Start

Use this skill when a new repository or conversation needs the correct SummitHarness journey before Ralph should run.

## Goal

Choose the right top-level workflow profile, lock the onboarding answers, and make sure the harness starts in the right stage instead of jumping straight into coding.

## Workflow

1. Read the current prompt, repo state, and any supplied materials first.
2. If the current repo looks like the SummitHarness source or plugin repo itself, do not assume it should be bootstrapped in place. First distinguish between:
   - improving the harness itself
   - using the harness in a separate target project
3. Decide which workflow profile best fits the request:
   - `proposal-only`: reviewer-facing document or submission first
   - `planning-only`: PRD, task graph, and approval package first
   - `build-direct`: idea is already locked and implementation should start quickly
   - `idea-to-service`: idea discovery through design and implementation in one journey
4. Ask only the minimum onboarding questions needed to lock:
   - final deliverable
   - whether ideation is still open
   - which domains are in scope
   - who approves the path
   - what evidence bar defines honest completion
5. If the answers are not explicit yet, stop there and wait. Do not choose a workflow profile or goal sentence by guess.
6. Run `python3 scripts/summit_start.py init --profile <profile> --goal "<goal>"` only after the workflow profile, goal, scope, and evidence bar are explicit or user-confirmed.
7. Fill `.codex-loop/workflow/ONBOARDING.md` and `.codex-loop/workflow/IDEAS.md` with the final answers and chosen direction.
8. Initialize or refresh intake and research docs for the active stage mode.
9. Refresh the compressed context and state clearly which stage is active, which stages come next, and whether task seeding should already happen.

## Rules

- Do not force `implementation` mode just because the repo contains code.
- Do not force `build-direct` just because the repo contains a codebase.
- Do not seed the task graph while the workflow is still in onboarding, idea exploration, or pre-research stages.
- If the user only wants one slice, choose the smallest profile that still fits honestly.
- Do not treat draft approval files as real approvals. Leave approval state pending until the user actually confirms the path.
