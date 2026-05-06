---
description: 모드에 맞는 인테이크 Q&A를 진행하고 첫 seed 실행 전에 승인 상태를 잠급니다.
---

# /summit-intake

브레인스토밍, 기획, 혹은 첫 자율 Ralph 실행 전에 사용합니다.

## 진행 순서

1. `scripts/summit_intake.py`가 있는지 확인합니다.
2. 인테이크 문서의 모드가 맞지 않으면 `python3 scripts/summit_intake.py init --mode <proposal|prd|implementation|product-ui>`를 실행합니다.
3. `.codex-loop/intake/QUESTIONNAIRE.md`를 읽고, 아직 답하지 않은 질문만 진행합니다.
4. 최종 Q&A를 `.codex-loop/intake/ANSWERS.md`에 기록합니다.
5. 목표, 범위, 산출물, 필수 증거 기준을 `.codex-loop/intake/APPROVAL.md`에 잠급니다.
6. 요청자가 실제로 승인했을 때만 `상태: 승인`과 `승인: 예`로 바꿉니다.
7. `python3 scripts/context_engine.py refresh --source intake`를 실행합니다.

## 참고

- 인테이크 승인이 잠기기 전에는 첫 seed 실행을 시작하면 안 됩니다.
- 브레인스토밍은 이제 승인된 인테이크를 더 정교하게 다듬는 단계이며, 추측으로 대체하는 단계가 아닙니다.
