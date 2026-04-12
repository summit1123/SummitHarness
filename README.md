# SummitHarness

`SummitHarness`는 Codex에서 쓸 수 있는 오픈소스 제품 개발 하네스입니다.

핵심은 단순한 retry loop가 아니라, 아래를 하나로 묶는 것입니다.

- PRD와 task 기반 구현 루프
- 압축 컨텍스트 엔진
- preflight 환경 점검
- 디자인/자산 파이프라인
- review gate와 deterministic checks
- Stop-hook 기반 same-session loop

즉 목표는 "기획서 넣으면 그럴듯한 코드"가 아니라, **기획 -> 디자인 방향 -> 자산 -> 구현 -> 평가 -> handoff**까지 이어지는 재사용 가능한 Codex 하네스를 만드는 것입니다.

## 지금 들어있는 것

```text
SummitHarness/
├── plugins/codex-ralph-loop/
├── personal-skills/
├── docs/
├── install.py
└── install.sh
```

실제 공개용 플러그인 번들은 [plugins/codex-ralph-loop](plugins/codex-ralph-loop/README.md) 에 있습니다.

## v2 방향

현재 하네스는 다섯 축으로 움직입니다.

1. `preflight`
2. `context-engine`
3. `visual-assets`
4. `implementation-loop`
5. `evaluation-gates`

이 구조 덕분에 긴 작업에서도 매 iteration마다 전체 로그를 다시 넣지 않고, `.codex-loop/context/handoff.md` 같은 압축 packet으로 이어갈 수 있습니다.

## 설치

```bash
git clone https://github.com/summit1123/SummitHarness.git
cd SummitHarness
python3 install.py
```

이 명령은 아래를 수행합니다.

1. 플러그인을 `~/.codex/plugins/codex-ralph-loop`에 복사
2. `~/.agents/plugins/marketplace.json` 갱신
3. `~/.codex/config.toml`에서 `codex_hooks = true` 보장
4. `~/.codex/hooks.json`에 Stop dispatcher 설치
5. `personal-skills/` 아래의 개인 스킬이 있으면 `~/.agents/skills/`에 연결

설치 후 Codex 재시작이 필요할 수 있습니다.

## 대상 프로젝트 bootstrap

작업할 저장소에서:

```bash
python3 ~/.codex/plugins/codex-ralph-loop/scripts/bootstrap_project.py .
python3 scripts/preflight.py run
python3 scripts/context_engine.py refresh --source bootstrap
```

처음 bootstrap 직후의 `.codex-loop/tasks.json`은 샘플 그래프입니다.
실제 goal은 `.codex-loop/prd/PRD.md`, `.codex-loop/prd/SUMMARY.md`, `.codex-loop/config.json`에 적고, 첫 `./ralph.sh --once` 실행에서 Ralph가 이 템플릿 task를 프로젝트 전용 task graph로 자동 교체합니다.

이제 프로젝트에는 아래가 생깁니다.

- `.codex-loop/prd/`
- `.codex-loop/tasks.json`
- `.codex-loop/context/`
- `.codex-loop/assets/registry.json`
- `.codex-loop/preflight/`
- `scripts/codex_ralph.py`
- `scripts/context_engine.py`
- `scripts/preflight.py`
- `scripts/asset_registry.py`
- `ralph.sh`

## 사용자는 어떻게 쓰나

실제 사용 흐름은 아래처럼 이해하면 됩니다.

1. `SummitHarness`를 한 번 설치합니다.
2. 작업할 저장소를 bootstrap합니다.
3. `.codex-loop/prd/PRD.md`와 `SUMMARY.md`에 goal과 제약을 적습니다.
4. `.codex-loop/config.json`에 실제 로컬 검증 명령을 넣습니다.
5. preflight를 돌려 환경 문제를 먼저 봅니다.
6. context engine이 현재 상태를 `handoff.md`로 압축합니다.
7. 첫 `./ralph.sh` 또는 `/ralph-loop` 실행에서 Ralph가 goal 기반 task graph를 자동 생성한 뒤 바로 첫 실행을 시작합니다.

사용자 입장에서 중요한 건 네 파일입니다.

- `.codex-loop/prd/PRD.md`: 무엇을 만들지
- `.codex-loop/preflight/REPORT.md`: 지금 돌릴 수 있는 환경인지
- `.codex-loop/context/handoff.md`: 지금 뭘 해야 하는지
- `.codex-loop/tasks.json`: Ralph가 현재 goal을 어떻게 작업 그래프로 해석했는지

즉 사용자는 긴 로그를 다 읽지 않아도 되고, 하네스가 압축해둔 현재 packet만 보면 다음 행동을 이해할 수 있습니다.

## 사용자에게 어떻게 안내되나

처음 쓰는 사람은 보통 아래 두 방식 중 하나로 시작합니다.

### 1. 터미널 방식

```bash
python3 ~/.codex/plugins/codex-ralph-loop/scripts/bootstrap_project.py .
python3 scripts/preflight.py run
python3 scripts/context_engine.py refresh --source bootstrap
./ralph.sh --once
```

### 2. Codex 프롬프트 방식

```text
Use $ralph-bootstrap to initialize this repository for SummitHarness.
Then run python3 scripts/preflight.py run.
Then run python3 scripts/context_engine.py refresh --source bootstrap.
Then update .codex-loop/prd/PRD.md, .codex-loop/prd/SUMMARY.md, and .codex-loop/config.json with the real goal and checks.
After that, let the first Ralph run auto-generate the task graph from the PRD.
```

slash command가 보이면 아래처럼 더 짧게도 갑니다.

```text
/init-codex-ralph
/summit-preflight
/summit-context-refresh
/run-codex-ralph
```

## 내부에서는 어떻게 처리되나

실제로는 아래 순서로 돌아갑니다.

1. installer가 플러그인을 home-local Codex plugin으로 등록합니다.
2. bootstrap이 현재 repo에 `.codex-loop/`, `scripts/`, `.codex/commands/`를 심습니다.
3. preflight가 툴체인, hooks, config, media 관련 준비 상태를 검사합니다.
4. context engine이 PRD, task, 최근 로그, 승인 자산을 읽고 `handoff.md`를 만듭니다.
5. loop runner가 이 handoff packet을 포함한 prompt로 worker를 실행합니다.
6. checks와 review gate가 실행되고 결과가 로그로 남습니다.
7. 다음 iteration 전에는 다시 context engine이 repo 상태를 압축합니다.
8. same-session hook loop라면 Stop hook이 `ralph-loop.json` 상태를 보고 continuation prompt를 다시 넣습니다.

핵심은 raw transcript를 매번 다 넣지 않고, **repo state -> compressed handoff -> next iteration** 구조로 계속 이어진다는 점입니다.

## 사용자가 중간에 보는 것

loop가 도는 동안 사용자는 주로 아래를 봅니다.

- `.codex-loop/context/handoff.md`: 다음 best step
- `.codex-loop/logs/LOG.md`: iteration별 요약
- `.codex-loop/reviews/`: read-only review 결과
- `.codex-loop/history/`: worker 실행 로그
- `.codex-loop/assets/registry.json`: 어떤 시각 자산이 승인됐는지

즉 이 하네스는 "그냥 한 번 실행하고 기다리는 스크립트"가 아니라, **중간 상태를 계속 확인할 수 있는 작업판**에 가깝습니다.

## Codex에서 바로 넘기는 프롬프트

### bootstrap

```text
Use $ralph-bootstrap to initialize this repository for SummitHarness.
```

### PRD/task 생성

```text
Use $ralph-prd to turn these requirements into .codex-loop/prd/PRD.md and .codex-loop/tasks.json.
```

직접 task graph를 먼저 잡고 싶을 때 쓰는 흐름이고, 비워두면 첫 Ralph run이 PRD를 바탕으로 자동 seed를 수행합니다.

### preflight와 context refresh

```text
Run python3 scripts/preflight.py run and then python3 scripts/context_engine.py refresh --source manual.
```

### loop 실행

```text
Use $codex-ralph-loop to run the project-local SummitHarness loop from the current PRD, tasks, and compressed context files.
```

### same-session hook loop

```text
/ralph-loop "Build the next vertical slice. Emit <promise>COMPLETE</promise> only when truly done." --completion-promise "<promise>COMPLETE</promise>" --max-iterations 20
```

## 왜 context engine이 중요한가

이 하네스에서 memory는 유저용 메모장이 아닙니다.

- raw 로그는 그대로 남기고
- 그중 다음 iteration에 필요한 것만 압축하고
- 오래 가야 하는 사실만 durable facts로 승격합니다

즉 `OpenClaw` 류의 context compression 감각에 더 가깝습니다.

## 디자인이 AI같지 않게 하려면

이 저장소는 디자인을 바로 JSX로 뽑는 대신, 아래 흐름을 권장합니다.

1. visual direction 정리
2. 이미지/영상/레퍼런스 자산 생성 또는 수집
3. 승인된 자산을 registry에 등록
4. 필요하면 Figma로 정리
5. 구현 루프는 승인된 방향을 기준으로만 진행

이미지/영상/Figma 연결은 환경에 따라 Codex의 `imagegen`, `sora`, `figma-implement-design` 워크플로와 연결할 수 있습니다.

## 품질 게이트

현재 공개 저장소 기준 기본 검증 경로는 아래입니다.

```bash
python3 -m unittest discover -s tests -v
```

GitHub Actions에서도 같은 smoke suite가 자동으로 돌게 되어 있습니다: [ci.yml](.github/workflows/ci.yml)

## 설치 백업과 복구

`python3 install.py`는 이제 사용자 로컬 설정을 건드리기 전에 backup manifest를 남깁니다.

설치 출력에 backup 경로와 restore 명령이 함께 표시됩니다.

예:

```bash
python3 ~/.codex/plugins/codex-ralph-loop/scripts/restore_install_backup.py <backup-dir>
```

즉 설치가 마음에 들지 않거나 환경이 꼬였을 때, 기존 `config.toml`, `hooks.json`, marketplace, 이전 plugin install tree를 되돌릴 수 있습니다.

## 문서

- [Architecture](docs/ARCHITECTURE.md)
- [User Flow](docs/USER_FLOW.md)
- [Plugin README](plugins/codex-ralph-loop/README.md)

## 라이선스

[MIT](LICENSE)
