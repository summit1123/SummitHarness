# Codex Ralph Loop / SummitHarness Plugin

이 플러그인은 Ralph loop 호환성을 유지하면서도, 이제 **SummitHarness 스타일의 오픈소스 제품 하네스**로 확장되는 방향을 갖습니다.

## 핵심 기능

- project-local PRD/task runtime
- compressed context engine
- preflight environment checks
- approved asset registry
- deterministic checks + read-only review gate
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

## slash command

- `/init-codex-ralph`
- `/run-codex-ralph`
- `/ralph-loop ...`
- `/cancel-ralph`
- `/summit-preflight`
- `/summit-context-refresh`

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
