---
name: ralph-start
description: Use when the user says "ralph start", "Ralph start", "start Ralph", "ralph onboarding", or asks to begin SummitHarness/Ralph onboarding in plain text instead of using a slash command.
---

# Ralph Start

This is a natural-language alias for the Summit Start workflow.

When this skill triggers, follow `plugins/codex-ralph-loop/skills/summit-start/SKILL.md` exactly:

1. Ask what the user wants to do in this run and where the run should stop.
2. Do not choose a workflow profile by guess.
3. Continue onboarding until goal, scope, approval path, evidence bar, and workflow profile are explicit.
4. Only then run `python3 scripts/summit_start.py init --profile <profile> --goal "<goal>"`.
5. Initialize or refresh intake/research docs and context for the active stage.

`ralph start` is intentionally not a command to immediately run the loop. It starts the onboarding/interview path that decides whether Ralph should later run as proposal, planning, direct build, or idea-to-service.
