# SummitHarness Architecture

## 목표

SummitHarness는 Codex용 오픈소스 제품 하네스다.

단순한 에이전트 재시도 루프가 아니라, 아래 요소를 하나로 묶습니다.

- 요구사항 인테이크
- PRD / task 분해
- 압축 컨텍스트 handoff
- 사전 점검
- 제출 PDF 게이트
- 시각 자산 파이프라인
- MCP 스타일 stage gate 산출물과 자동 pass/fail 판정
- 구현 루프
- evaluator 게이트

## 핵심 디렉토리

```text
.codex-loop/
├── intake/
│   ├── QUESTIONNAIRE.md
│   ├── ANSWERS.md
│   └── APPROVAL.md
├── research/
│   ├── PLAN.md
│   ├── FINDINGS.md
│   └── APPROVAL.md
├── prd/
├── tasks.json
├── tasks/
├── context/
│   ├── durable.json
│   ├── open-questions.json
│   ├── current-state.md
│   ├── handoff.md
│   └── events.jsonl
├── assets/
│   └── registry.json
├── stage-gates/
│   ├── spec.json
│   ├── artifacts/
│   └── results/
├── artifacts/
│   └── pdf-review/
├── preflight/
│   ├── status.json
│   └── REPORT.md
├── logs/
├── history/
└── reviews/
```

## 실행 모델

### 0. 인테이크 / 승인

`python3 scripts/summit_intake.py init --mode <...>`

첫 seed 실행 전에 역할별 질문지와 승인 문서를 잠급니다.

- 요청자 / 제품 관련 질문
- 모드별 디자인 또는 엔지니어링 질문
- 승인 권한자
- 잠긴 목표 / 산출물 / 비범위 / 증거 기준

승인이 잠기지 않으면 첫 task seed는 시작하지 않습니다.

### 0.5. 리서치 / 기획 게이트

`python3 scripts/summit_research.py init --mode <...>`

인테이크 승인 뒤에는 단계형 deep research를 잠급니다.

- 조사할 질문
- 수집할 근거
- 비교할 선택지
- 권장 방향
- 단계형 실행 계획

research approval이 잠기지 않으면 첫 task seed는 시작하지 않습니다.

### 1. 사전 점검

`python3 scripts/preflight.py run`

환경과 연결 상태를 확인합니다.

- Codex CLI
- Git / Python / Node toolchain
- Stop-hook 활성화 여부
- rmcp_client 여부
- Figma MCP 흔적
- `OPENAI_API_KEY`
- ffmpeg

### 2. 컨텍스트 압축

`python3 scripts/context_engine.py refresh`

저장소 상태를 바탕으로 다음 반복용 패킷을 만듭니다.

- 현재 task
- 열린 task
- 최신 체크 / 리뷰
- 승인된 asset
- 유지 제약사항
- 최근 진행 상황
- 열린 질문
- 다음 권장 단계

### 3. 시각 자산 파이프라인

`python3 scripts/asset_registry.py add ...`

승인된 이미지/영상/Figma/source를 기록한다.

이 registry는 구현 단계가 "현재 승인된 시각 방향"을 잊지 않게 한다.

### 4. All-rounder stage gate

`python3 scripts/ralph_stage_gate.py evaluate --stage <stage> --artifact <artifact.json>`

Public all-rounder Ralph는 아래 stage를 자동 gate로 다룬다.

```text
onboarding -> interview -> seed/PRD -> research -> design -> R&D -> dev -> eval
```

각 stage는 JSON artifact를 남기고, gate는 아래 기준을 기계적으로 검사한다.

- 요구사항 매핑 100%
- 핵심 claim/decision별 evidence 1개 이상
- critical/high 이슈 0개
- research/design/R&D score >= 0.85
- dev/eval score >= 0.90
- medium 이슈 허용량 준수 및 residual risk 기록
- 사용자 승인 누락, 테스트 실패, evidence 없는 핵심 결정, 요구사항 누락은 hard fail

실패 시 결과 JSON에는 `failureCauses`, `remediationPlan`, `rollbackTarget`이 기록된다. 같은 stage는 최대 2회 재시도하고, 이후에는 원인에 따라 `research`, `r-and-d`, `interview_or_seed_prd`, `user_judgment_gate` 중 하나로 보낸다.

### 5. 제출 PDF 게이트

`python3 scripts/review_submission_pdf.py path/to/proposal.pdf`

계획서나 제출용 첨부 PDF를 한 번 더 점검한다.

- `.pdf` 확장자 확인
- 파일명 쉼표 여부 확인
- 업로드 용량 제한 확인
- `pdfinfo`, `pdftotext` 기반 메타데이터/미리보기 추출
- 결과를 `.codex-loop/artifacts/pdf-review/`에 저장

이 gate는 "문서는 그럴듯한데 실제 제출물은 아직 틀린 상태"를 loop 바깥에서 먼저 잡아준다.

### 6. 구현 루프

`./ralph.sh` (default until-complete) / `./ralph.sh --once` (smoke/debug only)

외부 worker loop는 다음을 사용한다.

- PRD
- task spec
- compressed handoff
- deterministic checks
- read-only review gate

현재 이 repo는 첫 runnable loop slice를 검증하는 중이므로, task graph와 handoff가 실제 state와 일치하는지 확인하는 것이 우선이다.

### 7. Stop-hook 루프

`/ralph-loop ...`

same-session self-loop이며, `.codex-loop/ralph-loop.json`을 기준으로 계속 이어진다.

## 설계 원칙

1. raw transcript를 다시 전부 넣지 않는다.
2. 다음 턴에 필요한 packet만 handoff로 압축한다.
3. durable facts만 오래 남긴다.
4. 디자인은 코드보다 먼저 결정한다.
5. 평가기는 기능 평가와 시각 평가를 둘 다 담당한다.
6. 프로젝트별 runtime state와 reusable plugin bundle을 분리한다.

## 사용자 관점 실행 흐름

### 설치 이후

사용자는 `python3 install.py`를 한 번 실행합니다.

이때 내부에서는:

- plugin bundle 복사
- marketplace 등록
- `codex_hooks` 활성화
- global Stop dispatcher 등록

이 일어납니다.

### 대상 저장소에서

사용자는 보통 아래만 실행합니다.

```bash
python3 ~/.codex/plugins/codex-ralph-loop/scripts/bootstrap_project.py .
python3 scripts/preflight.py run
python3 scripts/summit_intake.py init --mode <...>
python3 scripts/summit_research.py init --mode <...>
python3 scripts/ralph_stage_gate.py init
python3 scripts/context_engine.py refresh --source bootstrap
```

이후 `./ralph.sh` 또는 `/ralph-loop ...`를 실행합니다.

### 사용자가 체감하는 산출물

사용자는 raw transcript 대신 아래를 중심으로 확인합니다.

- `preflight/REPORT.md`
- `context/handoff.md`
- `artifacts/pdf-review/`
- `logs/LOG.md`
- `reviews/`
- `assets/registry.json`
- `stage-gates/results/*-latest.json`

즉 SummitHarness는 실행기라기보다, 중간 상태를 계속 드러내는 작업 보드에 가깝습니다.
