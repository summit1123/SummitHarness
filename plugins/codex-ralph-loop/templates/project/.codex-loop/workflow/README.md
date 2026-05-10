# 워크플로우

이 폴더는 SummitHarness의 상위 진행 경로를 정리하는 곳입니다.

- `ONBOARDING.md`: 프로필별 온보딩 질문과 이번 런의 확정 결정
- `IDEAS.md`: 필요 시 아이디어 옵션 비교와 선택 메모
- `PROFILE.md`: 선택한 워크플로우 프로필과 단계 맵
- `STATUS.md`: 현재 단계, 다음 단계, task seed 준비 여부

권장 시작점은 `ralph start` 또는 `/ralph start`입니다. 이 단계에서는 먼저 사용자가 이번 런에서 무엇을 원하는지, 어디까지 진행하면 멈춰도 되는지, 어떤 증거가 있어야 완료인지 묻습니다.

`python3 scripts/summit_start.py init --profile <proposal-only|planning-only|build-direct|idea-to-service>` 는 온보딩 답변과 승인 기준이 명확해진 뒤 문서를 생성할 때만 사용합니다. profile과 goal을 추측해서 바로 실행하면 안 됩니다.
