# Codex Ralph Loop / SummitHarness Plugin

이 플러그인은 Ralph loop 호환성을 유지하면서도, 이제 **SummitHarness 스타일의 오픈소스 제품 하네스**로 확장되는 방향을 갖습니다.

## 핵심 기능

- project-local PRD/task runtime
- compressed context engine
- preflight environment checks
- approved asset registry
- deterministic checks + read-only review gate + goal evaluator
- Stop-hook same-session loop

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
- `.codex-loop/assets/registry.json`
- `.codex-loop/preflight/`
- `scripts/codex_ralph.py`
- `scripts/context_engine.py`
- `scripts/preflight.py`
- `scripts/asset_registry.py`
- `scripts/ralph_session.py`
- `ralph.sh`

## 추천 순서

```bash
python3 ~/.codex/plugins/codex-ralph-loop/scripts/bootstrap_project.py .
python3 scripts/preflight.py run
python3 scripts/context_engine.py refresh --source bootstrap
./ralph.sh --once
```

처음 bootstrap 직후의 task graph는 템플릿입니다. 실제 goal은 `.codex-loop/prd/PRD.md`, `.codex-loop/prd/SUMMARY.md`, `.codex-loop/config.json`에 적고, 첫 Ralph run이 그 내용을 바탕으로 task graph를 자동 재작성합니다.

## slash command

설치형 플러그인에서 바로 보이는 전역 명령과, bootstrap 이후 repo 안에 심어지는 project-local 명령이 함께 들어 있습니다.

- `/init-codex-ralph`
- `/summit-brainstorm`
- `/summit-write-plan`
- `/run-codex-ralph`
- `/ralph-loop ...`
- `/cancel-ralph`
- `/summit-preflight`
- `/summit-context-refresh`

## 실제 사용자 흐름

처음 쓰는 사용자는 보통 아래 순서로 씁니다.

1. 플러그인 설치
2. 대상 repo bootstrap
3. PRD/SUMMARY와 로컬 checks 설정
4. preflight 실행
5. context refresh
6. 첫 `./ralph.sh` 또는 `/ralph-loop` 실행
7. Ralph가 task graph를 auto-seed하고 계속 진행
8. Goal evaluator가 매 iteration마다 실제 목표 충족 여부를 다시 판단

가장 먼저 확인해야 하는 파일은 아래 다섯 가지입니다.

- `.codex-loop/prd/PRD.md`
- `.codex-loop/preflight/REPORT.md`
- `.codex-loop/context/handoff.md`
- `.codex-loop/tasks.json`
- `.codex-loop/evals/`

이 파일들이 각각 목표, 환경 상태, 다음 행동, 작업 그래프를 보여줍니다.

## 내부 처리 구조

사용자가 명령을 치면 내부에서는 이렇게 진행됩니다.

1. bootstrap이 runtime 파일을 repo 안에 복사
2. preflight가 toolchain과 config 상태 점검
3. context engine이 repo state를 압축
4. loop runner가 handoff packet을 포함한 prompt로 worker 실행
5. checks, review gate, goal evaluator 실행
6. 필요하면 replanning pass가 task graph를 보정
7. 로그와 state 저장
8. 다음 iteration 전 handoff 재생성

즉 사용자는 짧은 명령만 치지만, 하네스 내부에서는 `preflight -> compression -> execution -> evaluation -> refresh` 순환이 계속 일어납니다.

## 검증

로컬에서 기본 smoke suite를 돌릴 수 있습니다.

```bash
python3 -m unittest discover -s tests -v
```

GitHub Actions도 같은 흐름으로 `py_compile + unittest`를 돌립니다: [ci.yml](../../.github/workflows/ci.yml)

## 설치 백업과 복구

installer는 이제 plugin install tree, marketplace, `config.toml`, `hooks.json`을 수정하기 전에 backup manifest를 남깁니다.

설치 출력에 restore 명령이 함께 표시되며, 복구는 아래 스크립트로 할 수 있습니다.

```bash
python3 scripts/restore_install_backup.py <backup-dir>
```

## 이 플러그인이 지향하는 것

이 플러그인은 단순한 "반복 실행기"보다 더 큰 범위를 봅니다.

- PRD와 task가 실제 구현 상태와 어긋나지 않게 유지
- 긴 컨텍스트를 handoff packet으로 압축
- 디자인이 generic AI 느낌이면 visual input을 먼저 보강
- 승인된 이미지/영상/Figma 자산을 registry에 기록
- 구현 전에 환경과 연결 상태를 먼저 확인

## 관련 파일

- [plugin.json](.codex-plugin/plugin.json)
- [bootstrap_project.py](scripts/bootstrap_project.py)
- [context_engine.py](templates/project/scripts/context_engine.py)
- [preflight.py](templates/project/scripts/preflight.py)
- [asset_registry.py](templates/project/scripts/asset_registry.py)
