# SummitHarness Architecture

## 목표

SummitHarness는 Codex용 오픈소스 제품 하네스다.

단순한 agent retry loop가 아니라, 아래를 묶는다.

- requirement intake
- PRD / task decomposition
- compressed context handoff
- preflight validation
- visual asset pipeline
- implementation loop
- evaluator gates

## 핵심 디렉토리

```text
.codex-loop/
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
├── preflight/
│   ├── status.json
│   └── REPORT.md
├── logs/
├── history/
└── reviews/
```

## 실행 모델

### 1. Preflight

`python3 scripts/preflight.py run`

환경과 연결 상태를 확인한다.

- Codex CLI
- Git / Python / Node toolchain
- Stop-hook 활성화 여부
- rmcp_client 여부
- Figma MCP 흔적
- `OPENAI_API_KEY`
- ffmpeg

### 2. Context Compression

`python3 scripts/context_engine.py refresh`

repo 상태에서 다음 iteration용 packet을 만든다.

- active task
- open tasks
- latest checks/review
- approved assets
- durable constraints
- recent progress
- open questions
- next best step

### 3. Visual Asset Pipeline

`python3 scripts/asset_registry.py add ...`

승인된 이미지/영상/Figma/source를 기록한다.

이 registry는 구현 단계가 "현재 승인된 시각 방향"을 잊지 않게 한다.

### 4. Implementation Loop

`./ralph.sh`

외부 worker loop는 다음을 사용한다.

- PRD
- task spec
- compressed handoff
- deterministic checks
- read-only review gate

### 5. Stop-hook Loop

`/ralph-loop ...`

same-session self-loop이며, `.codex-loop/ralph-loop.json`을 기준으로 계속 이어진다.

## 설계 원칙

1. raw transcript를 다시 전부 넣지 않는다.
2. 다음 턴에 필요한 packet만 handoff로 압축한다.
3. durable facts만 오래 남긴다.
4. 디자인은 코드보다 먼저 결정한다.
5. 평가기는 기능 평가와 시각 평가를 둘 다 담당한다.
6. 프로젝트별 runtime state와 reusable plugin bundle을 분리한다.

## 사용자 관점의 실행 흐름

### 설치 이후

사용자는 `python3 install.py`를 한 번 실행합니다.

이때 내부에서는:

- plugin bundle 복사
- marketplace 등록
- `codex_hooks` 활성화
- global Stop dispatcher 등록

이 일어납니다.

### 대상 repo에서

사용자는 보통 아래만 실행합니다.

```bash
python3 ~/.codex/plugins/codex-ralph-loop/scripts/bootstrap_project.py .
python3 scripts/preflight.py run
python3 scripts/context_engine.py refresh --source bootstrap
```

이후 `./ralph.sh` 또는 `/ralph-loop ...`를 실행합니다.

### 사용자가 체감하는 산출물

사용자는 raw transcript 대신 아래를 중심으로 확인합니다.

- `preflight/REPORT.md`
- `context/handoff.md`
- `logs/LOG.md`
- `reviews/`
- `assets/registry.json`

즉 SummitHarness는 실행기라기보다, 중간 상태를 계속 드러내는 작업 보드에 가깝습니다.
