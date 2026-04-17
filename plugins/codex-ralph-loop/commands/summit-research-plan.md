---
description: task seed 전에 단계형 deep research 계획을 만들고 승인 상태를 잠급니다.
---

# /summit-research-plan

인테이크 승인 이후, 첫 자율 Ralph 실행 전에 사용합니다.

## 진행 순서

1. `scripts/summit_research.py`가 있는지 확인합니다.
2. 리서치 문서의 모드가 맞지 않으면 `python3 scripts/summit_research.py init --mode <proposal|prd|implementation|product-ui>`를 실행합니다.
3. 단계형 리서치 경로를 `.codex-loop/research/PLAN.md`에 작성합니다.
4. 수집 근거, 기각한 선택지, 다음 단계로 넘길 리스크를 `.codex-loop/research/FINDINGS.md`에 정리합니다.
5. 권장 방향과 실행 단계를 `.codex-loop/research/APPROVAL.md`에 잠급니다.
6. 리서치 방향이 실제로 승인되었을 때만 `상태: 승인`과 `승인: 예`로 바꿉니다.
7. `python3 scripts/context_engine.py refresh --source research`를 실행합니다.

## 참고

- 리서치 승인이 잠기기 전에는 첫 seed 실행을 시작하면 안 됩니다.
- 이 단계에서 하네스는 즉시 코딩보다 deep research에 가까운 방식으로 움직입니다.
