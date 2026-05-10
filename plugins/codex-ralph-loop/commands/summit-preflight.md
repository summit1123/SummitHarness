---
description: Ralph 실행 전에 현재 프로젝트의 환경, 훅, 도구 준비 상태를 점검합니다.
---

# /summit-preflight

Run the SummitHarness environment checks for the current project.

## Workflow

1. Confirm `scripts/preflight.py` exists.
2. Run `python3 scripts/preflight.py run`.
3. Summarize blockers and warnings from `.codex-loop/preflight/REPORT.md`.
4. If blockers exist, stop and tell the user what to fix first.
