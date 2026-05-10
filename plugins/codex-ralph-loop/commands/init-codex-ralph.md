---
description: 현재 프로젝트에 SummitHarness 실행 파일과 초기 작업 흐름 문서를 설치합니다.
---

# /init-codex-ralph

현재 프로젝트에 SummitHarness 런타임 파일을 설치합니다.

이 명령은 온보딩을 대신하지 않습니다. 설치 후에는 `ralph start` 또는 `/ralph start`로 사용자가 원하는 목표와 멈출 지점을 먼저 확인해야 합니다.

## Workflow

1. `python3 ~/.codex/plugins/codex-ralph-loop/scripts/bootstrap_project.py .`를 실행합니다.
2. `python3 scripts/preflight.py run`으로 환경을 확인합니다.
3. `ralph start` 또는 `/ralph start`로 온보딩을 시작합니다.
4. 사용자가 이번 런에서 무엇을 원하는지와 어디에서 멈추면 되는지 묻습니다.
5. profile, goal, task graph를 추측으로 고르지 않습니다.
6. profile, goal, scope, approval path, evidence bar가 명확해진 뒤에만 `python3 scripts/summit_start.py init --profile <proposal-only|planning-only|build-direct|idea-to-service> --goal "<goal>"`를 실행합니다.
7. `.codex-loop/workflow/ONBOARDING.md`를 채우고, 필요하면 `.codex-loop/workflow/IDEAS.md`도 정리합니다.
8. `python3 scripts/summit_intake.py init --mode <proposal|prd|implementation|product-ui>`를 실행합니다.
9. 요청자 Q&A를 `.codex-loop/intake/ANSWERS.md`에 기록하고 `.codex-loop/intake/APPROVAL.md`에서 승인을 잠급니다.
10. `python3 scripts/summit_research.py init --mode <proposal|prd|implementation|product-ui>`를 실행합니다.
11. 단계형 리서치 계획을 작성하고 `.codex-loop/research/APPROVAL.md`에서 승인을 잠급니다.
12. 승인된 목표와 리서치 방향에 맞춰 `.codex-loop/prd/PRD.md`와 `.codex-loop/prd/SUMMARY.md`를 다시 씁니다.
13. 기존 기획서나 제출 PDF가 있다면 `python3 scripts/review_submission_pdf.py "<path-to-pdf>"`를 실행합니다.
14. `python3 scripts/context_engine.py refresh --source bootstrap`로 컨텍스트를 갱신합니다.
15. `.codex-loop/config.json`에 실제 build, lint, test, screenshot 명령을 추가합니다.
16. `./ralph.sh` 또는 `/ralph-loop ...`를 시작합니다. `--once`는 smoke/debug용으로만 사용합니다.
17. 첫 Ralph 실행은 workflow, intake, research가 정렬된 뒤 bootstrap template task를 프로젝트 전용 task graph로 교체합니다.

## Notes

- Use `--force` only when you intentionally want to replace existing runtime files.
- The plugin stays reusable; the seeded `.codex-loop/` becomes project-owned state.
- If the current repo is the SummitHarness source/plugin repo itself, do not run this in place unless the user explicitly wants to modify the harness inside that repo.
