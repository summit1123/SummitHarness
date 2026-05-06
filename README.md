# SummitHarness

`SummitHarness`는 Codex용 Ralph-style 하네스입니다.
반복 실행 자체보다, **무엇을 만들고 있는지에 따라 루프의 판단 기준을 바꾸는 것**에 초점을 둡니다.

제안서는 제안서답게, PRD는 PRD답게, 구현은 구현답게, UI는 실제 제품 화면답게 다뤄야 합니다. `SummitHarness`는 그 차이를 workflow, mode, source of truth, evaluator, design contract에 모두 반영합니다.

## 왜 필요한가

기본적인 반복 루프만으로는 아래 문제가 자주 생깁니다.

1. 산출물 종류를 구분하지 못합니다.
- 제안서도 코드처럼 다루고, UI도 문서처럼 다룹니다.
- 그래서 완료 판정이 엉성해집니다.

2. 원본보다 포장만 만지게 됩니다.
- 문서 작업은 PDF만 고치고 Markdown source는 빈약한 채로 남습니다.
- UI 작업은 실제 흐름보다 카드 몇 장과 장식만 늘어납니다.

3. evaluator가 현재 task만 보고 끝났다고 착각합니다.
- 목표가 안 끝났는데 task list만 정리되면 완료처럼 보일 수 있습니다.

4. 컨텍스트가 길어질수록 작업이 흐려집니다.
- 승인 기준, 현재 단계, 남은 증거가 분리되어 있으면 loop가 헤매기 쉽습니다.

`SummitHarness`는 이 문제를 막기 위해 만들어졌습니다.

## 무엇이 달라졌나

### 1. workflow profile을 먼저 고릅니다
이번 런이 어떤 여정인지부터 잠급니다.

- `proposal-only`: 제출용 문서와 첨부 패키지 중심
- `planning-only`: PRD와 task graph 중심
- `build-direct`: 이미 잠긴 아이디어를 바로 구현
- `idea-to-service`: 아이디어 탐색부터 디자인, 개발, 검증까지 end-to-end

즉 `mode`보다 한 단계 위의 경로를 먼저 고정하고, 현재 stage에 맞는 mode가 따라오게 합니다.

### 2. 바로 task graph를 만들지 않습니다
seed 전에 두 개의 게이트를 먼저 잠급니다.

- 인테이크 Q&A와 승인 문서
- 단계형 research plan, findings, recommended direction

이 과정을 거치면 첫 task graph부터 훨씬 덜 흔들립니다.

### 3. mode별 source of truth가 다릅니다

- `proposal`: `docs/submissions/proposal.md` + design contract + PRD
- `prd`: `PRD.md`, `SUMMARY.md`, `tasks.json`, `TASK-*.json`
- `implementation`: codebase + tests + local checks + PRD
- `product-ui`: design contract + reference pack + approved assets + screenshots + actual UI

### 4. 문서는 source-first로 처리합니다
문서 작업은 `proposal.md -> source review -> render -> pdf review` 순서로 흘러갑니다.
PDF는 패키징 결과물이지, 내용의 원본이 아닙니다.

### 5. 디자인도 계약으로 다룹니다
디자인은 감으로 맡기지 않습니다.

- `Preset`: 큰 방향
- `Reference-Pack`: 프로젝트에 맞는 시각 레퍼런스 계열
- `Project-Specific Rules`: 이번 작업 전용 금지/필수 규칙

### 6. evaluator가 goal과 task drift를 같이 봅니다
현재 task만 보는 것이 아니라, 실제 목표와 task graph가 어긋났는지 같이 봅니다. 필요하면 replanning으로 이어집니다.

### 7. 긴 런을 위한 압축 컨텍스트를 유지합니다
`handoff`, `workflow`, `intake`, `research`, `PRD`, `design`, `logs`가 서로 어긋나지 않도록 압축 패킷을 계속 갱신합니다.

## 빠른 시작

### 설치

```bash
git clone https://github.com/summit1123/SummitHarness.git
cd SummitHarness
python3 install.py
```

### 프로젝트 bootstrap

작업할 저장소에서:

```bash
python3 ~/.codex/plugins/codex-ralph-loop/scripts/bootstrap_project.py .
python3 scripts/preflight.py run
python3 scripts/summit_start.py init --profile <proposal-only|planning-only|build-direct|idea-to-service> --goal "<goal>"
python3 scripts/summit_intake.py init --mode <proposal|prd|implementation|product-ui>
python3 scripts/summit_research.py init --mode <proposal|prd|implementation|product-ui>
```

## 권장 진행 순서

1. `.codex-loop/workflow/ONBOARDING.md`에 이번 런의 목표, 범위, 승인권자, evidence bar를 적습니다.
2. 아이디어가 열려 있으면 `.codex-loop/workflow/IDEAS.md`에서 옵션을 비교하고 하나를 고릅니다.
3. `.codex-loop/intake/ANSWERS.md`와 `.codex-loop/intake/APPROVAL.md`로 요청자 Q&A와 승인 기준을 잠급니다.
4. `.codex-loop/research/PLAN.md`, `FINDINGS.md`, `APPROVAL.md`로 research 방향과 단계별 실행안을 잠급니다.
5. `.codex-loop/prd/PRD.md`, `SUMMARY.md`, `.codex-loop/design/DESIGN.md`를 승인된 방향에 맞게 정리합니다.
6. 필요하면 `.codex-loop/design/reference-packs/`에서 pack을 고르거나 프로젝트 전용으로 복제합니다.
7. proposal 작업이면 `docs/submissions/proposal.md`를 먼저 씁니다.
8. source review, render, pdf review 순서로 검수합니다.
9. `python3 scripts/context_engine.py refresh --source bootstrap`로 handoff를 갱신합니다.
10. 기본 실행은 `./ralph.sh`입니다. `--once`는 smoke 또는 디버그용 1회 실행일 뿐이고, 실제 Ralph 런은 완료될 때까지 계속 도는 기본 실행을 권장합니다.

## 제안서 작업 예시

```bash
python3 scripts/review_submission_source.py docs/submissions/proposal.md
python3 scripts/render_markdown_submission.py
python3 scripts/review_submission_pdf.py output/pdf/proposal.pdf
python3 scripts/context_engine.py refresh --source bootstrap
./ralph.sh
```

`./ralph.sh --once`는 seed나 환경 확인용 smoke run입니다. 실제 Ralph 런은 기본값인 `./ralph.sh`로 시작하는 편이 맞습니다.

## 반복 정책

기본 루프는 이제 `until-complete`입니다.

- 템플릿 기본값은 `max_iterations: 0`, `iteration_policy: until_complete`입니다.
- `-n` 또는 `--max-iterations`를 직접 넘긴 경우에만 bounded loop로 잠깁니다.
- seed가 한 번 실패해도 바로 종료하지 않고, 재시도 후에도 task graph가 비어 있으면 로컬 recovery seed를 생성해 Ralph가 다음 작업으로 넘어갑니다.
- `--once`는 디버그용 예외 경로입니다.

## 실제 실행 중 보게 되는 것

기본 실행인 `./ralph.sh`를 돌리면 seed, worker, review, evaluator, replan phase가 각각 로그를 남깁니다.

- `.codex-loop/history/seed-worker.log`
- `.codex-loop/history/iteration-*-worker.log`
- `.codex-loop/reviews/iteration-*-review.log`
- `.codex-loop/evals/iteration-*-eval.log`

실행이 길어지면 heartbeat가 추가되고, timeout이 나면 해당 로그 파일 경로와 함께 실패가 기록됩니다.

## bootstrap 이후 주로 보게 되는 파일

- `.codex-loop/workflow/`: 상위 여정과 현재 stage
- `.codex-loop/intake/`: 요청자 Q&A와 승인 문서
- `.codex-loop/research/`: research plan, findings, approved direction
- `.codex-loop/prd/`: PRD와 요약
- `.codex-loop/tasks.json`, `.codex-loop/tasks/`: 현재 task graph
- `.codex-loop/context/handoff.md`: 지금 이어서 봐야 할 압축 상태
- `.codex-loop/evals/`: evaluator 결과
- `.codex-loop/artifacts/source-review/`: 원고 리뷰 결과
- `.codex-loop/artifacts/pdf-review/`: PDF 리뷰 결과
- `.codex-loop/assets/registry.json`: 승인된 asset 목록
- `.codex-loop/stage-gates/`: all-rounder Ralph의 JSON stage artifacts, gate spec, 평가 결과

## 레퍼런스 팩

기본 제공 pack은 아래 경로에 있습니다.

[design-reference-packs](/Users/gimdonghyeon/Desktop/SummitHarness/plugins/codex-ralph-loop/design-reference-packs)

예를 들면:

- `editorial-signal`
- `security-console`
- `citizen-service`
- `consumer-trust`
- `devtool-minimal`
- `impeccable-operator`
- `impeccable-consumer`
- `impeccable-responsive`

## 개인화

`personal-skills/summit-ralph-personal/`에는 사용자 취향 overlay가 들어갑니다.

예: AI 같은 문체 금지, sparse page 금지, decorative circle/card spam 금지, PDF-only fix 금지, 표와 비교와 근거 우선.

## 검증

```bash
python3 -m unittest discover -s tests -v
```

플러그인 사용 흐름은 [plugins/codex-ralph-loop/README.md](/Users/gimdonghyeon/Desktop/SummitHarness/plugins/codex-ralph-loop/README.md)에서 이어집니다.
