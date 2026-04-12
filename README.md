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

## Codex에서 바로 넘기는 프롬프트

### bootstrap

```text
Use $ralph-bootstrap to initialize this repository for SummitHarness.
```

### PRD/task 생성

```text
Use $ralph-prd to turn these requirements into .codex-loop/prd/PRD.md and .codex-loop/tasks.json.
```

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

## 문서

- [Architecture](docs/ARCHITECTURE.md)
- [Plugin README](plugins/codex-ralph-loop/README.md)

## 라이선스

[MIT](LICENSE)
