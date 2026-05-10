---
name: ralph-start
description: 사용자가 ralph start 또는 Ralph 온보딩 시작을 요청할 때 목표 확인과 시작 흐름을 여는 진입점입니다.
---

# Ralph Start

`ralph start`의 역할은 실행이 아니라 온보딩입니다.

이 skill이 트리거되면 `plugins/codex-ralph-loop/skills/summit-start/SKILL.md`를 그대로 따르세요.

## 반드시 지킬 것

1. 먼저 사용자가 이번 런에서 무엇을 하고 싶은지, 어디까지 하면 멈춰도 되는지 묻습니다.
2. 답변이 부족하면 profile, goal, task를 추측하지 말고 온보딩 질문을 계속합니다.
3. 목표, 범위, 산출물, 승인 경로, 완료 증거 기준, workflow profile이 명확해질 때까지 Ralph 루프를 시작하지 않습니다.
4. 위 정보가 명확하거나 사용자가 방금 승인했을 때만 `python3 scripts/summit_start.py init --profile <profile> --goal "<goal>"`를 실행합니다.
5. 그 뒤에 intake, research, context 문서를 초기화하거나 갱신합니다.

## 첫 응답에서 물어야 하는 핵심

- 이번 런에서 만들거나 정리하고 싶은 최종 결과물은 무엇입니까?
- 이번 런은 어디까지 진행하면 충분합니까?
- 아이디어 탐색, 기획서, PRD, 디자인, 프론트엔드, 백엔드, AI 모듈, 배포 중 어디까지 포함합니까?
- 이미 있는 입력 자료는 무엇입니까? 예: repo, 공모전 요강, PDF, Figma, 스크린샷, 기존 PRD
- 이번 작업이 완료됐다고 판단할 증거는 무엇입니까?
- 사용자가 직접 승인해야 하는 지점은 어디입니까?

`ralph start`는 즉시 loop를 돌리는 명령이 아닙니다. proposal, planning, direct build, idea-to-service 중 어떤 여정으로 갈지 정하는 인터뷰 입구입니다.
