# Codex Ralph Loop / SummitHarness Plugin

이 플러그인은 Codex 안에서 장시간 루프를 돌리되, **작업 종류에 따라 source of truth와 completion gate를 다르게 적용하는 하네스**입니다.

핵심은 “계속 다시 시키기” 자체가 아니라, **무엇을 만들고 있는지에 따라 루프의 판단 기준을 바꾸는 것**입니다.

## 왜 이 플러그인이 필요한가

기본적인 Ralph-style loop는 반복에는 강하지만, 실제 작업에서는 아래 문제가 생깁니다.

- proposal 작업인데 PDF만 만집니다.
- UI 작업인데 디자인 근거 없이 카드 몇 장으로 끝납니다.
- evaluator가 task list만 보고 완료라고 착각합니다.
- 디자인이 매번 비슷한 AI 산출물로 수렴합니다.
- PRD, tasks, docs, code가 서로 어긋납니다.

이 플러그인은 그 문제를 막기 위해 아래 구조를 넣었습니다.

## 핵심 구조

- project-local PRD / task runtime
- compressed context engine
- preflight environment checks
- mode contracts
- design contract
- reference-pack design layer
- Markdown source review gate
- Markdown -> HTML / PDF renderer
- final PDF attachment gate
- approved asset registry
- deterministic checks + read-only review gate + goal evaluator
- Stop-hook same-session loop

즉, proposal이면 source review가 먼저고, product-ui면 design contract와 reference pack이 먼저입니다.

## mode별 source of truth

- `proposal`: `docs/submissions/proposal.md` + design contract + PRD
- `prd`: `PRD.md`, `SUMMARY.md`, `tasks.json`
- `implementation`: codebase + tests + checks + PRD
- `product-ui`: design contract + reference pack + approved assets + screenshots + actual UI

## 디자인 레이어

디자인은 이제 아래 3단계로 다룹니다.

1. `Preset`
- 문서형인지 제품형인지 같은 큰 방향

2. `Reference-Pack`
- 프로젝트에 맞는 시각 reference family
- anti-pattern, hierarchy, spacing, tone을 구체화

3. `Project-Specific Rules`
- 이번 작업에서 금지할 것 / 꼭 지킬 것

### 왜 reference pack이 필요한가

그냥 “예쁘게 만들어라”라고 하면 루프는 자주 아래로 무너집니다.

- nested card
- vague spacing
- decorative accent overuse
- generic SaaS AI style
- mobile/desktop hierarchy 붕괴
- 증거 없는 screenshot 위주 polish

그래서 SummitHarness는 reference pack을 먼저 고르게 합니다.

### 어떤 레퍼런스를 반영했나

- `awesome-design-md`: reusable design prompt / contract 발상
- `impeccable`: anti-pattern 방지, hierarchy, polish, responsive discipline 발상

둘 다 그대로 복사한 것이 아니라, SummitHarness workflow에 맞게 pack으로 재구성했습니다.

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

- `.codex-loop/prd/`
- `.codex-loop/tasks.json`
- `.codex-loop/context/`
- `.codex-loop/evals/`
- `.codex-loop/design/DESIGN.md`
- `.codex-loop/design/reference-packs/`
- `.codex-loop/modes/`
- `.codex-loop/assets/registry.json`
- `.codex-loop/preflight/`
- `docs/submissions/proposal.md`
- `scripts/codex_ralph.py`
- `scripts/context_engine.py`
- `scripts/preflight.py`
- `scripts/asset_registry.py`
- `scripts/review_submission_source.py`
- `scripts/render_markdown_submission.py`
- `scripts/review_submission_pdf.py`
- `ralph.sh`

## 추천 사용 순서

```bash
python3 ~/.codex/plugins/codex-ralph-loop/scripts/bootstrap_project.py .
python3 scripts/preflight.py run
```

그다음:

1. `PRD`, `SUMMARY`, `DESIGN.md`를 실제 목표에 맞게 수정
2. `Reference-Pack` 선택
3. proposal이면 Markdown source 먼저 작성
4. source review 통과
5. render 후 PDF gate 실행
6. context refresh
7. Ralph 실행
8. evaluator가 목표와 task drift를 계속 다시 판단

## proposal 흐름

```bash
python3 scripts/review_submission_source.py docs/submissions/proposal.md
python3 scripts/render_markdown_submission.py
python3 scripts/review_submission_pdf.py output/pdf/proposal.pdf
python3 scripts/context_engine.py refresh --source bootstrap
./ralph.sh --once
```

## slash command

- `/init-codex-ralph`
- `/summit-brainstorm`
- `/summit-write-plan`
- `/summit-preflight`
- `/summit-review-doc`
- `/summit-render-doc`
- `/summit-review-pdf`
- `/summit-context-refresh`
- `/run-codex-ralph`
- `/ralph-loop ...`
- `/cancel-ralph`

## 검증

```bash
python3 -m unittest discover -s tests -v
```

## 지향점

이 플러그인의 목표는 하나입니다.

- proposal은 proposal답게
- PRD는 PRD답게
- 구현은 구현답게
- product-ui는 실제로 보기 싫지 않게

즉 같은 Ralph loop라도, **mode contract + design contract + reference pack + quality bar**가 같이 먹도록 만드는 구조입니다.
