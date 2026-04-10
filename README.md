# SummitHarness

`SummitHarness`는 Codex에서 바로 쓸 수 있는 Ralph loop를 플러그인 번들 형태로 배포하기 위한 저장소입니다.

이 저장소는 두 가지를 함께 다룹니다.

- 누구나 설치할 수 있는 공개용 플러그인
- 본인 취향과 작업 방식만 담는 개인용 오버레이 스킬

## 저장소 구조

```text
SummitHarness/
├── .agents/plugins/marketplace.json
├── plugins/codex-ralph-loop/
├── personal-skills/
├── install.py
└── install.sh
```

## 플러그인에 들어있는 것

실제로 배포되는 플러그인은
[`plugins/codex-ralph-loop/`](./plugins/codex-ralph-loop/README.md)에 있습니다.

이 번들에는 아래가 포함됩니다.

- PRD 작성, runtime loop 실행, 디자인 게이트, 리뷰 게이트용 `skills/`
- 명시적으로 진입할 수 있는 `commands/`
- 대상 프로젝트를 초기화하는 `templates/project/`
- 설치 스크립트와 bootstrap 스크립트
- 플러그인 에셋과 가벼운 hook 설정

## 여기서 말하는 배포란?

이 저장소에서 배포는 npm 배포보다 GitHub에 소스를 공개하고, 다른 사용자가 아래 흐름으로 쓰게 하는 것을 뜻합니다.

1. 저장소 clone
2. 설치 스크립트 실행
3. Codex 재시작
4. 대상 프로젝트 bootstrap
5. `./ralph.sh` 실행

즉 이 저장소는 npm 패키지라기보다 플러그인 소스 저장소에 가깝습니다. 나중에 npm 래퍼를 붙일 수는 있지만, 실제 설치 단위는 여전히 플러그인 디렉터리입니다.

## Codex에 설치하기

저장소를 clone한 뒤 루트에서 실행:

```bash
python3 install.py
```

이 명령은 세 가지를 수행합니다.

1. `plugins/codex-ralph-loop/`를 `~/.codex/plugins/codex-ralph-loop`로 복사
2. `~/.agents/plugins/marketplace.json` 갱신
3. `personal-skills/` 아래의 유효한 스킬을 `~/.agents/skills/`로 symlink 또는 copy

개인용 오버레이 없이 공개 플러그인만 설치하고 싶다면:

```bash
python3 install.py --no-personal-skills
```

설치 후 Codex에서 바로 보이지 않으면 재시작하면 됩니다.

## Codex에 바로 넘기는 방법

설치가 끝났다고 해서 Codex가 자동으로 loop를 시작하는 건 아닙니다. 처음에는 아래 프롬프트를 그대로 붙여 넣는 방식이 가장 안정적입니다.

### 1. 현재 프로젝트 bootstrap

작업할 기존 저장소를 Codex로 연 다음, 아래를 그대로 붙여 넣으세요.

```text
Use $ralph-bootstrap to initialize this repository for Codex Ralph loop.
```

slash command가 보이는 surface라면 아래처럼 시작해도 됩니다.

```text
/init-codex-ralph
```

### 2. 기획을 PRD와 task로 변환

bootstrap이 끝나면 아래처럼 요구사항을 넘깁니다.

```text
Use $ralph-prd to turn these requirements into .codex-loop/prd/PRD.md and .codex-loop/tasks.json.

Requirements:
- ...
- ...
```

### 3. loop 실행

PRD와 task를 확인한 뒤에는 아래처럼 실행합니다.

```text
Use $codex-ralph-loop to run the project-local Ralph loop from the current PRD and task files.
```

또는 slash command가 보이면:

```text
/run-codex-ralph
```

### 4. 한 번에 넘기고 싶다면

아래 프롬프트 하나로 시작해도 됩니다.

```text
Use $ralph-bootstrap to initialize this repository for Codex Ralph loop.
Then use $ralph-prd to convert my requirements into .codex-loop/prd/PRD.md and .codex-loop/tasks.json.
After that, review the generated task breakdown with me before running the loop.
```

이 문단 자체는 README에서 복사해서 Codex에 바로 붙여 넣는 용도로 넣어둔 것입니다.

## 설치 후 무슨 일이 일어나나

설치가 끝나면 Codex는 아래를 인식할 수 있습니다.

- 플러그인 manifest
- 번들된 plugin skills
- plugin commands
- `personal-skills/`에서 설치된 개인용 스킬

중요한 점은 설치만으로 loop가 시작되지는 않는다는 거예요. 설치는 Codex가 이 workflow를 사용할 수 있게 만드는 단계입니다.

## 대상 프로젝트 bootstrap

대상 저장소 안에서 실행:

```bash
python3 ~/.codex/plugins/codex-ralph-loop/scripts/bootstrap_project.py .
```

이 명령으로 아래 파일들이 생성됩니다.

- PRD, task, steering, logs, state를 담는 `.codex-loop/`
- `scripts/codex_ralph.py`
- `scripts/import_hwpx_preview.py`
- `ralph.sh`
- loop 관련 `.gitignore` 항목

그 다음 PRD와 task를 채운 뒤 아래처럼 실행하면 됩니다.

```bash
./ralph.sh --once
```

하지만 실제 사용감은 터미널에서 직접 bootstrap 명령을 치는 것보다, 위의 "Codex에 바로 넘기는 방법" 섹션에 있는 프롬프트를 Codex에 붙여 넣는 쪽이 더 자연스럽습니다.

## 저장소 자체를 Codex에서 열었을 때

이 저장소에는 [`/.agents/plugins/marketplace.json`](./.agents/plugins/marketplace.json)도 포함되어 있어서, `SummitHarness` 자체를 Codex에서 열면 home-local 설치를 하지 않아도 repo-local plugin으로 인식될 수 있습니다.

## 개인용 오버레이 스킬

공개 플러그인은 최대한 범용적으로 유지하고, 너무 개인적인 취향이나 작업 방식은 [`personal-skills/`](./personal-skills/README.md)에 두는 것을 권장합니다.

예를 들면:

- 더 빡센 리뷰 기준
- 더 강한 제품 감각 기준
- 선호하는 아키텍처 기본값
- 개인적인 escalation 규칙

이 스킬들은 공개 플러그인의 계약 일부가 아니라, `~/.agents/skills/`에 설치되는 사용자 전용 오버레이입니다.

## 참고 문서

- [Codex plugins](https://developers.openai.com/codex/plugins/build)
- [Codex skills](https://developers.openai.com/codex/skills)
- [Codex hooks](https://developers.openai.com/codex/hooks)
