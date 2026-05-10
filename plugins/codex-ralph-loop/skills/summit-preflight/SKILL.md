---
name: summit-preflight
description: 하네스 실행 전에 환경, Codex hook, 도구체인, MCP 힌트, 미디어 도구 준비 상태를 점검합니다.
---

# Summit Preflight

Use this skill before a long run or before attempting design-heavy automation.

## Workflow

1. Run `python3 scripts/preflight.py run`.
2. Read `.codex-loop/preflight/REPORT.md`.
3. Separate blockers from warnings.
4. Fix blockers before starting autonomous implementation.
5. If design or media workflows matter, call out missing Figma, ffmpeg, or API-key prerequisites.
