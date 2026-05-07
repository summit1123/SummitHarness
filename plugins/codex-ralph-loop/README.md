# Codex Ralph Loop / SummitHarness Plugin

이 플러그인은 Codex 안에서 장시간 loop를 돌리되, **작업 종류에 따라 source of truth와 completion gate를 다르게 적용하는 하네스**입니다.

핵심은 반복 자체가 아니라, 지금 다루는 산출물이 proposal인지, PRD인지, 구현인지, product-ui인지에 따라 판단 기준을 바꾸는 것입니다.

## 이 플러그인이 필요한 이유

기본적인 Ralph-style loop만으로는 아래 문제가 자주 생깁니다.

- proposal 작업인데 PDF만 만지게 됩니다.
- UI 작업인데 디자인 근거 없이 카드와 장식만 늘어납니다.
- evaluator가 task list만 보고 완료라고 착각합니다.
- PRD, tasks, docs, code가 서로 어긋납니다.
- 긴 런에서 승인 기준과 현재 단계가 흐려집니다.

이 플러그인은 그 문제를 막기 위해 workflow, intake, research, contracts, context engine을 함께 묶습니다.

## 핵심 구조

- 워크플로우 온보딩과 프로필 선택
- 인테이크 질문지와 승인 게이트
- 단계형 deep research / direction lock
- 프로젝트 로컬 PRD / task runtime
- 압축 컨텍스트 엔진
- preflight 환경 점검
- mode contract
- design contract
- reference-pack 디자인 계층
- Markdown source review
- Markdown -> HTML / PDF 렌더
- 최종 PDF gate
- 승인된 asset registry
- local checks + read-only review + goal evaluator
- machine-readable stage gate artifacts and rollback routing
- Stop hook 기반 same-session loop

즉 proposal이면 source review가 먼저고, product-ui면 design contract와 reference pack이 먼저이며, implementation이면 checks와 codebase가 우선입니다.

## mode별 source of truth

- `proposal`: `docs/submissions/proposal.md` + design contract + PRD
- `prd`: `PRD.md`, `SUMMARY.md`, `tasks.json`, `TASK-*.json`
- `implementation`: codebase + tests + checks + PRD
- `product-ui`: design contract + reference pack + approved assets + screenshots + actual UI

## workflow profile

`mode`는 현재 단계의 실행 계약이고, `workflow profile`은 상위 여정입니다.

- `proposal-only`: 제출용 문서와 첨부 패키지 중심
- `planning-only`: PRD와 task graph 중심
- `build-direct`: 이미 잠긴 아이디어를 바로 구현
- `idea-to-service`: 인사이트 탐색 -> research -> PRD -> 디자인 -> 구현 -> 검증

하네스는 현재 workflow stage가 seed를 허용하는 단계인지도 함께 봅니다. 그래서 onboarding이나 research 단계에서는 task graph를 억지로 만들지 않습니다.

## all-rounder stage gates

Public all-rounder Ralph는 `onboarding -> interview -> seed/PRD -> research -> design -> R&D -> dev -> eval`을 하나의 자동 gate 흐름으로 다룹니다.

각 stage는 `.codex-loop/stage-gates/artifacts/` 아래에 JSON 산출물을 남기고, `scripts/ralph_stage_gate.py`가 다음 조건으로 pass/fail을 판정합니다.

- 요구사항 매핑 100%
- 핵심 결정마다 evidence 1개 이상
- critical/high 이슈 0개
- research/design/R&D 점수 0.85 이상
- dev/eval 점수 0.90 이상
- medium 이슈는 research/R&D 최대 2개, design/dev/eval 최대 1개
- medium 이슈가 있으면 residual risk 기록 필수
- 사용자 승인 누락, 테스트 실패, evidence 없는 핵심 결정, 요구사항 누락은 점수와 무관하게 hard fail

실패하면 원인별 remediation plan을 만들고 같은 stage를 최대 2회 재시도합니다. `orchestrate` 명령은 이전 실패 결과를 읽어 retry budget을 추적하고, 이후에는 실패 원인에 따라 `research`, `r-and-d`, `interview_or_seed_prd`, `user_judgment_gate`로 rollback합니다.

## 디자인 레이어

디자인은 아래 세 층으로 다룹니다.

1. `Preset`
- 문서형인지 제품형인지 같은 큰 방향

2. `Reference-Pack`
- 프로젝트에 맞는 시각 레퍼런스 계열
- hierarchy, density, anti-pattern, tone을 구체화

3. `Project-Specific Rules`
- 이번 작업에서 금지할 것과 꼭 지킬 것

그냥 “예쁘게 만들어라”라고 두면 loop는 쉽게 generic한 AI 결과물로 무너집니다. 그래서 레퍼런스 팩을 먼저 고르게 합니다.

## 설치

```bash
git clone https://github.com/summit1123/SummitHarness.git
cd SummitHarness
python3 install.py
```

또는 플러그인 디렉터리에서 직접:

```bash
python3 scripts/install_home_local.py
```

## 설치 시 실제로 일어나는 일

1. 플러그인 복사
2. marketplace 등록
3. `codex_hooks = true` 보장
4. 전역 Stop dispatcher 설치
5. 필요 시 개인 스킬 연결

## bootstrap 이후 프로젝트에 생기는 것

- `.codex-loop/workflow/`
- `.codex-loop/intake/`
- `.codex-loop/research/`
- `.codex-loop/prd/`
- `.codex-loop/tasks.json`
- `.codex-loop/context/`
- `.codex-loop/evals/`
- `.codex-loop/design/DESIGN.md`
- `.codex-loop/design/reference-packs/`
- `.codex-loop/assets/registry.json`
- `.codex-loop/stage-gates/spec.json`
- `.codex-loop/stage-gates/artifacts/`
- `.codex-loop/stage-gates/results/`
- `.codex-loop/preflight/`
- `docs/submissions/proposal.md`
- `scripts/codex_ralph.py`
- `scripts/context_engine.py`
- `scripts/preflight.py`
- `scripts/summit_start.py`
- `scripts/summit_intake.py`
- `scripts/summit_research.py`
- `scripts/review_submission_source.py`
- `scripts/render_markdown_submission.py`
- `scripts/review_submission_pdf.py`
- `ralph.sh`

## 추천 사용 순서

```bash
python3 ~/.codex/plugins/codex-ralph-loop/scripts/bootstrap_project.py .
python3 scripts/preflight.py run
# Codex 안에서는 `/ralph start` 또는 `/ralph-start`로 시작하는 것을 권장
python3 scripts/summit_start.py init --profile <proposal-only|planning-only|build-direct|idea-to-service> --goal "<goal>"
python3 scripts/summit_intake.py init --mode <proposal|prd|implementation|product-ui>
python3 scripts/summit_research.py init --mode <proposal|prd|implementation|product-ui>
python3 scripts/ralph_stage_gate.py init
```

그다음:

1. 먼저 사용자에게 이번 런에서 무엇을 하고 싶은지, 어디까지 진행하면 되는지 확인합니다.
2. workflow onboarding과 ideas를 정리합니다.
3. intake 질문지와 승인 문서를 잠급니다.
4. research plan, findings, recommended direction을 잠급니다.
5. PRD, SUMMARY, DESIGN.md를 현재 방향에 맞게 고칩니다.
6. reference pack을 선택합니다.
7. proposal이면 Markdown source부터 씁니다.
8. source review -> render -> pdf review 순서로 검수합니다.
9. context를 refresh합니다.
10. `python3 scripts/ralph_stage_gate.py orchestrate --start onboarding --end eval --requirement "<requirement>"`로 stage gate를 순서대로 checkpoint합니다. 단일 stage는 `checkpoint --stage <stage>`를 쓰고, 이미 worker가 custom artifact를 만들었다면 `evaluate --artifact <path>`를 사용합니다.
11. Ralph를 실행합니다.
12. evaluator가 goal과 task drift를 계속 다시 판단합니다.

## 제안서 흐름 예시

```bash
python3 scripts/review_submission_source.py docs/submissions/proposal.md
python3 scripts/render_markdown_submission.py
python3 scripts/review_submission_pdf.py output/pdf/proposal.pdf
python3 scripts/context_engine.py refresh --source bootstrap
./ralph.sh
```

## 타임아웃 정책

기본 timeout은 작업 성격에 따라 다르게 봐야 합니다. 특히 proposal / prd 기반의 deep research, 방향 비교, evaluator, replan은 3분 안에 끝나는 성격이 아닙니다.

현재 기본 정책은 아래처럼 완화되어 있습니다.

- proposal / prd: seed 15분, worker 30분, review 10분, evaluator 15분, replan 15분
- product-ui: seed 10분, worker 30분, review 10분, evaluator 10분, replan 10분
- implementation: seed 5분, worker 20분, review 5분, evaluator 5분, replan 5분

기존 프로젝트에 예전 기본값(`seed 180`, `review/evaluator/replan 300`)이 들어 있어도, 런타임에서 legacy preset으로 감지되면 더 긴 모드별 기본값으로 자동 승격합니다.

직접 조정하고 싶다면 `.codex-loop/config.json`의 `agent.timeout_seconds`를 수정하면 됩니다.

## 반복 정책

기본 루프는 `until-complete`입니다.

- 템플릿 기본값은 `max_iterations: 0`, `iteration_policy: until_complete`입니다.
- `-n` 또는 `--max-iterations`를 직접 넘긴 경우에만 bounded loop로 잠깁니다.
- seed가 한 번 실패해도 재시도 후 로컬 recovery seed를 생성해 다음 작업으로 넘어갑니다.
- `--once`는 smoke 또는 디버그용 예외 경로입니다.

## 실행 중 보게 되는 것

기본 실행인 `./ralph.sh`를 돌리면 seed, worker, review, evaluator, replan phase가 각각 로그를 남깁니다.

- `.codex-loop/history/seed-worker.log`
- `.codex-loop/history/iteration-*-worker.log`
- `.codex-loop/reviews/iteration-*-review.log`
- `.codex-loop/evals/iteration-*-eval.log`

실행이 길어지면 heartbeat가 추가되고, timeout이 나면 로그 파일 경로와 함께 실패가 기록됩니다.

## 슬래시 커맨드

- `/init-codex-ralph`
- `/ralph`
- `/ralph start`
- `/ralph run`
- `/ralph gate`
- `/ralph-start`
- `/summit-intake`
- `/summit-research-plan`
- `/summit-brainstorm`
- `/summit-write-plan`
- `/summit-preflight`
- `/summit-review-doc`
- `/summit-render-doc`
- `/summit-review-pdf`
- `/summit-context-refresh`
- `/run-codex-ralph`
- `/ralph-stage-gate`
- `/ralph-loop ...`
- `/cancel-ralph`

## 검증

```bash
python3 -m unittest discover -s tests -v
```

## 지향점

이 플러그인의 목표는 단순합니다.

- proposal은 proposal답게
- PRD는 PRD답게
- 구현은 구현답게
- product-ui는 실제 화면답게

즉 같은 Ralph loop라도, **mode contract + design contract + reference pack + quality bar**가 함께 먹는 구조를 만드는 것이 목적입니다.
