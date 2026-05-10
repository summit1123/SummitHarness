---
name: summit-start
description: 새 저장소나 새 대화에서 Ralph가 바로 달리지 않도록 목표, 범위, 승인 기준을 먼저 확인하는 시작 흐름입니다.
---

# Summit Start

Plain-text aliases: `ralph start`, `Ralph start`, `start Ralph`, `ralph onboarding`.

새 저장소나 새 대화에서 Ralph를 돌리기 전에, 먼저 올바른 여정과 멈출 지점을 잠그는 skill입니다.

## Goal

상위 workflow profile을 고르고, 온보딩 답변을 잠그고, 하네스가 바로 코딩으로 뛰어들지 않게 올바른 단계에서 시작하도록 만듭니다.

## Workflow

1. 현재 프롬프트, repo 상태, 첨부 자료를 먼저 확인합니다.
2. 현재 repo가 SummitHarness 소스나 플러그인 repo처럼 보이면, 그 자리에 bootstrap한다고 가정하지 않습니다. 먼저 아래 둘 중 무엇인지 구분합니다.
   - 하네스 자체를 개선하려는 것
   - 별도 대상 프로젝트에서 하네스를 쓰려는 것
3. 어떤 workflow profile도 결정하기 전에, 사용자가 이번 런에서 무엇을 하고 싶은지와 어디에서 멈추면 되는지를 평문으로 묻습니다.
4. 요청에 가장 맞는 workflow profile을 고릅니다.
   - `proposal-only`: reviewer-facing document or submission first
   - `planning-only`: PRD, task graph, and approval package first
   - `build-direct`: idea is already locked and implementation should start quickly
   - `idea-to-service`: idea discovery through design and implementation in one journey
5. 경로를 정말 잠그기 위한 온보딩 질문을 합니다. 요청이 흐릿하면 여러 번에 나누어 묻습니다. 최소한 아래를 확인합니다.
   - 최종 산출물
   - 아이디어 탐색이 아직 열려 있는지
   - 포함 범위: 기획서, PRD, 디자인, 프론트엔드, 백엔드, AI 모듈, 배포, 제출 패키징
   - 승인권자 또는 최종 의사결정자
   - 먼저 필요한 리서치 깊이와 근거 수집 방식
   - honest COMPLETE라고 부를 수 있는 증거 기준
6. 답변이 아직 명확하지 않으면 그 자리에서 멈추고 사용자 답변을 기다립니다. workflow profile, 목표 문장, 범위, 승인 경로, 증거 기준이 명확해질 때까지 온보딩을 계속합니다. profile이나 목표 문장을 추측으로 고르지 않습니다.
7. workflow profile, goal, scope, approval path, evidence bar가 명확하거나 사용자가 방금 확인한 뒤에만 `python3 scripts/summit_start.py init --profile <profile> --goal "<goal>"`를 실행합니다.
8. 최종 답변과 선택 방향을 `.codex-loop/workflow/ONBOARDING.md`와 `.codex-loop/workflow/IDEAS.md`에 기록합니다.
9. 현재 stage mode에 맞게 intake와 research 문서를 초기화하거나 갱신합니다.
10. 압축 context를 갱신하고 현재 stage, 다음 stage, task seed 가능 여부를 명확히 말합니다.

## Rules

- repo에 코드가 있다는 이유만으로 `implementation` mode를 강제하지 않습니다.
- repo에 코드베이스가 있다는 이유만으로 `build-direct`를 강제하지 않습니다.
- workflow가 onboarding, idea exploration, pre-research 단계에 있으면 task graph를 만들지 않습니다.
- 사용자가 한 조각만 원하면, 정직하게 맞는 가장 작은 profile을 고릅니다.
- 초안 approval 파일을 실제 승인으로 취급하지 않습니다. 사용자가 실제로 확인할 때까지 승인 상태는 pending으로 둡니다.
- 속도를 위해 온보딩을 압축하지 않습니다. 목표가 흐릿하면 Ralph를 돌리기 전에 계속 질문합니다.
