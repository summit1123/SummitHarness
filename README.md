# SummitHarness

`SummitHarness`는 Codex에서 장시간 작업을 자동 반복시키되, **산출물의 종류에 따라 다른 품질 기준을 적용하는 Ralph-style 하네스**입니다.

단순히 “계속 다시 시키는 루프”가 아니라,

- 제안서면 제안서답게
- PRD면 PRD답게
- 구현이면 구현답게
- UI면 UI답게

source of truth, 평가 기준, 검증 흐름을 바꾸는 것이 핵심입니다.

## 왜 필요한가

기존의 단순 에이전트 루프는 반복은 잘합니다. 하지만 실제 작업에서는 아래 문제가 자주 생깁니다.

1. 산출물 종류를 구분하지 못합니다.
- 제안서도 코드처럼 다루고, UI도 문서처럼 다룹니다.
- 그래서 완료 판정이 엉성해집니다.

2. PDF나 결과물만 만지다가 원본이 약해집니다.
- 문서 작업에서 자꾸 PDF만 고치고, 정작 Markdown source는 빈약한 상태로 남습니다.

3. 디자인이 반복적으로 비슷해집니다.
- 장식용 카드, 애매한 강조색, 허전한 레이아웃, 전형적인 AI 산출물 패턴으로 수렴합니다.

4. evaluator가 현실을 잘 못 봅니다.
- 실제 목표보다 현재 task 목록만 보고 끝났다고 착각할 수 있습니다.

`SummitHarness`는 이 문제를 막기 위해 만들어졌습니다.

## 무엇을 해결하나

### 1. mode-aware loop
작업 모드에 따라 source of truth와 quality bar를 다르게 적용합니다.

- `proposal`
- `prd`
- `implementation`
- `product-ui`

### 2. source-first document flow
문서 작업은 PDF가 아니라 Markdown 원본을 먼저 검수합니다.

`proposal.md -> source review -> render -> pdf review`

### 3. design contract + reference pack
디자인도 감으로 맡기지 않습니다.

- `Preset`: 큰 방향
- `Reference-Pack`: 프로젝트에 맞는 시각 레퍼런스 가족
- `Project-Specific Rules`: 이번 작업 전용 금지/필수 규칙

### 4. context compression
루프가 길어져도 현재 상태를 압축된 handoff로 유지합니다.

### 5. evaluator-driven replanning
목표에 아직 도달하지 않았는데 task graph가 현실과 어긋나면, evaluator가 replanning을 유도합니다.

## 핵심 구조

이 저장소는 현재 아래 축으로 동작합니다.

1. `preflight`
2. `context engine`
3. `mode contracts`
4. `design contract`
5. `reference-pack design layer`
6. `document source gate`
7. `render pipeline`
8. `implementation loop`
9. `review / evaluator gates`

## 디자인 레이어는 왜 따로 두는가

에이전트는 디자인 기준이 없으면 비슷한 실수를 반복합니다.

- nested card 남발
- decorative circle / pill / accent spam
- product screen인데 hero 레이아웃 사용
- weak hierarchy
- screenshot은 많은데 실제 근거는 없음
- “그럴듯한 SaaS”처럼 보이지만 실제론 빈약한 구조

그래서 SummitHarness는 디자인도 source처럼 다룹니다.

기본 제공 pack은 두 계열에서 영향을 받습니다.

- `awesome-design-md`: 문서/스타일 reference 발상
- `impeccable`: product-ui polish, anti-pattern, hierarchy discipline 발상

하지만 그대로 가져다 쓰지 않고, SummitHarness 작업 흐름에 맞게 다시 정리했습니다.

## 설치

```bash
git clone https://github.com/summit1123/SummitHarness.git
cd SummitHarness
python3 install.py
```

## bootstrap

작업할 저장소에서:

```bash
python3 ~/.codex/plugins/codex-ralph-loop/scripts/bootstrap_project.py .
python3 scripts/preflight.py run
```

그 다음 해야 할 일은 보통 이 순서입니다.

1. `.codex-loop/prd/PRD.md`와 `SUMMARY.md`를 실제 목표에 맞게 고칩니다.
2. `.codex-loop/design/DESIGN.md`에서 `Preset`과 `Reference-Pack`을 정합니다.
3. 필요하면 `.codex-loop/design/reference-packs/`의 pack을 복제해서 프로젝트 전용으로 수정합니다.
4. proposal 작업이면 `docs/submissions/proposal.md`부터 작성합니다.
5. source review -> render -> pdf review 순서로 검수합니다.
6. context를 refresh하고 Ralph를 시작합니다.

## proposal 흐름 예시

```bash
python3 scripts/review_submission_source.py docs/submissions/proposal.md
python3 scripts/render_markdown_submission.py
python3 scripts/review_submission_pdf.py output/pdf/proposal.pdf
python3 scripts/context_engine.py refresh --source bootstrap
./ralph.sh --once
```

## 실행 중 무엇을 보게 되나

`./ralph.sh --once`를 실행하면 이제 Codex가 끝날 때까지 조용히 멈춘 것처럼 보이지 않습니다.

- `.codex-loop/history/seed-worker.log` 또는 `iteration-*-worker.log`가 **실행 직후 바로 생성**됩니다.
- Codex가 오래 걸리면 로그에 heartbeat 줄이 주기적으로 추가됩니다.
- seed / worker / review / evaluator / replan phase는 각각 timeout을 가집니다.
- timeout이 나면 로그 파일 경로와 함께 명시적으로 실패합니다.

기본값은 `.codex-loop/config.json`의 `agent.timeout_seconds`와 `agent.heartbeat_seconds`로 조정할 수 있습니다.

## product-ui 흐름 예시

1. `loop.mode`를 `product-ui`로 설정
2. `Preset: product-ops`
3. 적절한 `Reference-Pack` 선택
4. 승인된 asset / screenshot 등록
5. 구현 후 스크린샷과 상태 증거를 남김
6. evaluator가 디자인 계약 위반까지 같이 봄

## bootstrap 이후 생기는 것

- `.codex-loop/prd/`
- `.codex-loop/tasks.json`
- `.codex-loop/context/`
- `.codex-loop/evals/`
- `.codex-loop/design/DESIGN.md`
- `.codex-loop/design/reference-packs/`
- `.codex-loop/assets/registry.json`
- `.codex-loop/preflight/`
- `docs/submissions/proposal.md`
- `scripts/context_engine.py`
- `scripts/review_submission_source.py`
- `scripts/render_markdown_submission.py`
- `scripts/review_submission_pdf.py`
- `ralph.sh`

## 사용자는 어디를 보면 되나

- `.codex-loop/context/handoff.md`: 지금 무엇이 가장 중요한지
- `.codex-loop/tasks.json`: 현재 남은 일의 구조
- `.codex-loop/evals/`: evaluator가 왜 아직 안 끝났다고 보는지
- `.codex-loop/artifacts/source-review/`: 문서 원본이 왜 막혔는지
- `.codex-loop/artifacts/pdf-review/`: 첨부 PDF가 왜 막혔는지
- `.codex-loop/assets/registry.json`: 어떤 자산이 승인되었는지

## reference pack

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

예:

- AI 같은 문체 금지
- sparse page 금지
- decorative circle/card spam 금지
- PDF-only fix 금지
- 표, 비교, 근거, 흐름 우선

## 검증

```bash
python3 -m unittest discover -s tests -v
```

플러그인 관점 설명은 [plugins/codex-ralph-loop/README.md](/Users/gimdonghyeon/Desktop/SummitHarness/plugins/codex-ralph-loop/README.md)에서 이어집니다.
