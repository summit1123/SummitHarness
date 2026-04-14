# SummitHarness

`SummitHarness`는 Codex에서 쓰는 오픈소스 제품 개발 하네스입니다.

핵심은 단순 retry loop가 아니라, **목표의 종류에 따라 source of truth와 완료 기준이 달라지는 Ralph-style harness**를 만드는 것입니다.

## 현재 방향

이 저장소는 지금 아래 축으로 움직입니다.

1. `preflight`
2. `context-engine`
3. `mode contracts`
4. `document source gate`
5. `reference-pack design layer`
6. `render pipeline`
7. `implementation loop`
8. `evaluation gates`

즉 proposal은 proposal답게, PRD는 PRD답게, 구현은 구현답게, UI는 UI답게 평가되도록 만드는 구조입니다.

## 가장 중요한 변화

디자인도 이제 `preset + reference pack + project-specific rules` 구조로 갑니다.

- `Preset`: 문서형인지 제품형인지 같은 큰 방향
- `Reference-Pack`: 프로젝트에 맞는 시각 레퍼런스 가족
- `Project-Specific Rules`: 이번 작업에서 금지할 것과 꼭 지킬 것

기본 제공 reference pack은 `awesome-design-md`에서 얻은 설계 감각을 우리 하네스 문법으로 다시 정리한 것입니다.

이제 proposal 류 산출물은:

- `PDF`가 source가 아님
- `docs/submissions/proposal.md`가 source of truth
- `review_submission_source.py`가 먼저 검수
- `render_markdown_submission.py`가 HTML/PDF로 패키징
- `review_submission_pdf.py`는 마지막 첨부 검수

이 순서로 갑니다.

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

proposal 흐름이면 먼저 `.codex-loop/design/DESIGN.md`에서 `Reference-Pack`을 고르고, 필요하면 `.codex-loop/design/reference-packs/`의 파일을 복제해 프로젝트 전용으로 수정한 뒤 이어서:

```bash
python3 scripts/review_submission_source.py docs/submissions/proposal.md
python3 scripts/render_markdown_submission.py
python3 scripts/review_submission_pdf.py output/pdf/proposal.pdf
```

그리고 Ralph 실행:

```bash
python3 scripts/context_engine.py refresh --source bootstrap
./ralph.sh --once
```

## 사용자는 뭘 보나

- `.codex-loop/context/handoff.md`: 지금 뭘 해야 하는지
- `.codex-loop/tasks.json`: Ralph가 남은 일을 어떻게 해석했는지
- `.codex-loop/evals/`: evaluator가 왜 아직 안 끝났다고 보는지
- `.codex-loop/artifacts/source-review/`: 문서 소스가 왜 막히는지
- `.codex-loop/artifacts/pdf-review/`: 첨부 PDF가 왜 막히는지
- `.codex-loop/assets/registry.json`: 어떤 자산이 승인됐는지

## 개인화 방향

`personal-skills/summit-ralph-personal/`에는 사용자 취향을 강하게 반영하는 overlay가 들어갑니다.

예를 들면:

- AI 같은 문체 금지
- sparse page 금지
- decorative circle/card spam 금지
- PDF-only fix 금지
- 실질적 표, 비교, 흐름, 근거 우선

## 검증

```bash
python3 -m unittest discover -s tests -v
```

플러그인 사용 README는 [plugins/codex-ralph-loop/README.md](plugins/codex-ralph-loop/README.md)에 있습니다.
