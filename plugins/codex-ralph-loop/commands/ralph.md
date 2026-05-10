---
description: /ralph 하위 명령을 온보딩, 실행, 검수, 취소 흐름으로 연결합니다.
---

# /ralph

Use this as the short public entrypoint for SummitHarness.

## Routing

- `/ralph start`: follow `/ralph-start` exactly. Treat it as a strict onboarding interview, not as a run command. Ask what the user wants to do in this run and where to stop, choose the workflow profile only after enough answers are explicit, then initialize `scripts/summit_start.py`.
- `/ralph run`: follow `/run-codex-ralph`. Refresh context, check intake/research/workflow gates, then run the project-local Ralph loop.
- `/ralph gate`, `/ralph checkpoint`, or `/ralph orchestrate`: follow `/ralph-stage-gate`. Run ordered stage checkpoints with `scripts/ralph_stage_gate.py orchestrate`, generate one stage with `checkpoint`, or evaluate an existing artifact with `evaluate`.
- `/ralph loop`: follow `/ralph-loop`. Use same-session Stop-hook looping.
- `/ralph cancel`: follow `/cancel-ralph`.

If the user types `/ralph` with no subcommand, treat it as `/ralph start` unless the current project already has an active `.codex-loop/ralph-loop.json` session, in which case summarize the active state and ask whether to continue, cancel, or start a new onboarding pass.

## Rules

- Do not skip or compress onboarding when routing to `start`.
- Do not infer approval from draft files.
- Do not start autonomous looping from `/ralph start`; only prepare the correct journey and next stage.
