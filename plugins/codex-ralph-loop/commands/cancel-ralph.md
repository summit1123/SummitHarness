---
description: 현재 프로젝트에서 실행 중인 중지 훅 기반 Ralph 루프를 취소합니다.
---

# /cancel-ralph

Cancel the hook-native Ralph loop in the current repository.

## Workflow

1. Confirm `scripts/ralph_session.py` exists.
2. Run `python3 scripts/ralph_session.py cancel`.
3. Summarize whether a loop was cancelled or no active loop existed.
