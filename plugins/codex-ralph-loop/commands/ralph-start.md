---
description: SummitHarness 온보딩을 시작하고 목표에 맞는 작업 흐름 유형과 Ralph 진행 경로를 정합니다.
---

# /ralph-start

플러그인 설치 후 새 프로젝트에 들어왔을 때 가장 먼저 쓰는 명령입니다.

`/ralph-start`의 목적은 루프 실행이 아니라 **강한 온보딩**입니다. 목표, 범위, 산출물, 승인 경로, 완료 증거 기준이 잠기기 전에는 task graph 생성이나 자율 Ralph 실행으로 넘어가면 안 됩니다.

## Workflow

1. 다른 작업보다 먼저 현재 repo, 첨부 자료, PDF, PRD, 사용자 프롬프트를 확인합니다.
2. 현재 repo가 SummitHarness 소스 자체이거나 `plugins/codex-ralph-loop/`를 가진 플러그인 repo처럼 보이면, 기본값으로 그 자리에 bootstrap하지 않습니다. 먼저 사용자가 원하는 것이 아래 둘 중 무엇인지 묻습니다.
   - 하네스 자체 개선
   - 별도 대상 프로젝트에서 하네스 사용
3. `scripts/summit_start.py`가 없고 현재 repo가 정상 대상 프로젝트인 것이 확인되면 `/init-codex-ralph`로 런타임을 설치할 수 있습니다. 단, 이 설치는 온보딩 문서를 만들기 위한 준비일 뿐, profile을 추측하거나 loop를 시작하는 승인이 아닙니다.
4. workflow profile을 고르기 전에 반드시 평문으로 묻습니다. “이번 런에서 무엇을 하고 싶은가요?”와 “어디까지 진행하면 멈춰도 될까요?”가 첫 질문입니다.
5. 이어서 충분히 깊은 구조화 Q&A를 진행합니다. 최소한 아래를 확인합니다.
   - `proposal-only`, `planning-only`, `build-direct`, `idea-to-service` 중 무엇에 가까운지
   - honest final deliverable이 무엇인지
   - 아이디어 탐색이 아직 필요한지
   - 디자인, 프론트엔드, 백엔드, AI 모듈, 제출 패키징이 범위에 포함되는지
   - 먼저 필요한 리서치 깊이, 참고자료, 근거 수집 방식은 무엇인지
   - 누가 방향을 승인하고, 어떤 증거가 있어야 COMPLETE라고 부를 수 있는지
6. 답변이 프롬프트나 첨부 자료에 이미 명확하지 않다면, 현재 온보딩 질문을 던진 뒤 멈추고 사용자 답변을 기다립니다. workflow profile, goal sentence, scope, evidence bar가 진짜로 잠길 때까지 여러 번에 나누어 온보딩을 계속합니다. `build-direct`, `idea-to-service` 또는 다른 profile을 추측으로 선택하지 않습니다.
7. workflow profile, goal sentence, scope, approval path, evidence bar가 이미 명확하거나 사용자가 방금 확인한 경우에만 `python3 scripts/summit_start.py init ...`를 실행합니다.
8. profile과 goal이 명확해진 뒤 `python3 scripts/summit_start.py init --profile <chosen-profile> --goal "<locked goal sentence>"`를 실행합니다.
9. 실제 답변을 `.codex-loop/workflow/ONBOARDING.md`에 기록하고, 아이디어 비교가 필요하면 `.codex-loop/workflow/IDEAS.md`에 옵션과 선택 이유를 기록합니다.
10. 현재 workflow stage에 맞게 intake와 research 문서를 초기화하거나 갱신하고, context packet을 갱신한 뒤 올바른 다음 stage를 요약합니다.
11. approval 문서를 실제 승인된 것처럼 쓰지 않습니다. 사용자가 실제로 확인할 때까지 pending 상태로 둡니다.
12. 사용자가 첫 stage를 정직하게 승인할 수 있을 정도로 명확해지기 전에는 자율 Ralph loop를 시작하지 않습니다. 온보딩 깊이가 속도보다 중요합니다.
13. 응답 마지막에는 항상 사용자가 직접 고르지 않아도 되도록 `다음에 입력할 명령: ...`을 적습니다. 보통 온보딩 직후에는 `다음에 입력할 명령: /summit-intake`입니다.

## Notes

- `workflow profile`은 상위 여정이고, `mode`는 현재 stage의 실행 계약입니다.
- `idea-to-service`는 사용자가 아이디어 탐색부터 제품 제작까지 한 하네스 안에서 원한다고 명시했을 때만 기본값처럼 다룹니다.
- `ralph start`는 “시작 버튼”이 아니라 “온보딩 인터뷰 시작”입니다.
