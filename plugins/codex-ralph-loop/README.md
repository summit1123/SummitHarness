# Codex Ralph Loop / SummitHarness Plugin

이 플러그인은 Ralph loop 호환성을 유지하면서도, 이제 **문서 소스부터 제품 구현까지 모드별로 다르게 움직이는 SummitHarness**를 목표로 합니다.

## 지금 핵심 구조

- project-local PRD/task runtime
- compressed context engine
- preflight environment checks
- Markdown source review gate
- reference-pack design layer
- Markdown -> HTML/PDF renderer
- final PDF attachment gate
- approved asset registry
- deterministic checks + read-only review gate + goal evaluator
- Stop-hook same-session loop

즉 핵심은 `PDF를 먼저 고치는 것`이 아니라, **source truth -> render -> final package** 순서를 강제하는 데 있습니다.

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

## 추천 순서

```bash
python3 ~/.codex/plugins/codex-ralph-loop/scripts/bootstrap_project.py .
python3 scripts/preflight.py run
python3 scripts/review_submission_source.py docs/submissions/proposal.md   # proposal mode일 때
python3 scripts/render_markdown_submission.py                              # proposal mode일 때
python3 scripts/review_submission_pdf.py output/pdf/proposal.pdf           # 최종 첨부 직전
python3 scripts/context_engine.py refresh --source bootstrap
./ralph.sh --once
```

## 모드별 source of truth

- `proposal`: `docs/submissions/proposal.md` + `.codex-loop/design/DESIGN.md`
- `prd`: `.codex-loop/prd/PRD.md`, `SUMMARY.md`, `tasks.json`
- `implementation`: codebase + tests + checks + PRD
- `product-ui`: design contract + approved assets + screenshots + actual UI

## 실제 사용자 흐름

1. 플러그인 설치
2. 대상 repo bootstrap
3. PRD/SUMMARY/DESIGN 계약 정리
4. `Reference-Pack` 선택 또는 프로젝트 전용 pack 생성
5. proposal이면 Markdown source부터 작성
6. source review 통과
7. render 후 final PDF gate 실행
8. context refresh
9. Ralph 실행
10. evaluator가 목표 충족과 task drift를 계속 다시 판단

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

## 이 플러그인이 지향하는 것

- goal이 proposal이면 proposal답게 평가
- goal이 PRD면 PRD답게 평가
- goal이 implementation이면 코드와 검증으로 평가
- goal이 product-ui면 디자인 계약과 시각 증거까지 같이 평가

즉 같은 Ralph loop라도 **mode contract와 quality bar가 다르게 먹는 구조**입니다.
