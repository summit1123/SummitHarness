# Codex Ralph Loop 플러그인

이 플러그인은 두 방식으로 사용할 수 있습니다.

- 현재 워크스페이스처럼 repo-local로 사용
- 누구나 설치할 수 있는 home-local 플러그인으로 사용

이 디렉터리 안에는 아래가 들어 있습니다.

- `skills/`: bootstrap, PRD 작업, runtime loop, design gate, review gate용 스킬
- `hooks.json`: Bash 실행 후 가벼운 리마인더를 주는 hook
- `assets/`: 플러그인 아이덴티티 에셋
- `templates/project/`: 대상 프로젝트에 심는 runtime 템플릿
- `scripts/bootstrap_project.py`: `.codex-loop/`, `ralph.sh` 등을 대상 프로젝트에 생성
- `scripts/install_home_local.py`: 플러그인을 `~/.codex/plugins/codex-ralph-loop`로 설치하고 `~/.agents/plugins/marketplace.json`을 갱신하며, 원하면 개인 스킬도 `~/.agents/skills`로 연결

반대로 아래 항목들은 대상 프로젝트 쪽에 생깁니다.

- PRD
- task graph
- steering notes
- run logs
- history
- review outputs

loop runner 자체는 project template로 제공됩니다. bootstrap 이후 대상 프로젝트는 자기 전용 `scripts/codex_ralph.py`와 `ralph.sh`를 갖게 됩니다.

## 설치

`SummitHarness` 저장소 기준으로 처음 설치할 때는 아래 순서로 실행하면 됩니다.

```bash
git clone https://github.com/summit1123/SummitHarness.git
cd SummitHarness
python3 install.py
```

플러그인 디렉터리 안에서 직접 설치하고 싶다면 아래도 가능합니다.

```bash
python3 scripts/install_home_local.py
```

그 다음 아무 대상 프로젝트에서:

```bash
python3 ~/.codex/plugins/codex-ralph-loop/scripts/bootstrap_project.py .
./ralph.sh --once
```

이 흐름이 이 플러그인을 일회성 실험이 아니라 재사용 가능한 plugin으로 만들어 줍니다.

## 여기서 말하는 배포란?

이 플러그인에서 배포는 보통 GitHub 저장소로 공개해서 다른 개발자가 clone 후 installer를 실행할 수 있게 하는 것을 뜻합니다.

일반적인 흐름은 이렇습니다.

1. 예를 들어 `SummitHarness` 같은 저장소에 이 플러그인을 올림
2. 사용자가 로컬에 clone
3. clone한 저장소에서 installer 실행
4. installer가 플러그인을 사용자 로컬 Codex plugin 영역에 복사하고 marketplace를 갱신
5. Codex가 번들된 skills를 발견

즉 npm 패키지와는 다릅니다. 나중에 npm 래퍼를 붙일 수는 있어도 실제 배포 단위는 이 plugin 폴더 자체입니다.

## 설치 시 실제로 일어나는 일

사용자가 아래 installer를 실행하면:

```bash
python3 scripts/install_home_local.py
```

아래 순서로 동작합니다.

1. `plugins/codex-ralph-loop/`를 `~/.codex/plugins/codex-ralph-loop`로 복사합니다.
2. `~/.agents/plugins/marketplace.json`에 플러그인을 등록합니다.
3. `~/.codex/config.toml`에 `codex_hooks = true`를 보장합니다.
4. `~/.codex/hooks.json`에 Ralph Stop hook dispatcher를 등록합니다.
5. 소스 저장소에 `personal-skills/`가 있으면 해당 스킬을 `~/.agents/skills/`로 symlink 또는 copy 합니다.
6. 바로 보이지 않으면 Codex를 재시작합니다.

설치가 끝나면 Codex는 아래를 인식할 수 있습니다.

- plugin manifest
- 번들된 `skills/`
- plugin `commands/`
- plugin assets와 helper scripts

중요한 점은 Codex가 플러그인을 하나의 거대한 프로그램처럼 실행하는 게 아니라는 것입니다. 번들된 skill들을 발견하고, 프롬프트나 워크스페이스 파일, 혹은 `$skill-name` 명시 호출과 맞을 때 해당 skill을 사용합니다.

## 설치 후 Codex 안에서는

설치가 끝나고 Codex에서 인식되면:

1. plugin에 번들된 skills를 명시적으로 사용할 수 있게 됩니다.
2. 같은 skills는 description과 metadata가 현재 작업과 맞을 때 암묵적으로도 호출될 수 있습니다.
3. `commands/`는 Codex surface에 따라 slash-command 스타일 진입점으로 보일 수 있습니다.
4. 다만 실제 loop를 돌리려면 bootstrap된 대상 프로젝트가 여전히 필요합니다.

즉 설치만으로 Ralph loop가 시작되지는 않습니다. 설치는 Codex가 이 workflow를 사용할 수 있게 만드는 단계입니다.

## Codex에 그대로 붙여 넣는 프롬프트

이 플러그인은 설치 후 README의 프롬프트를 그대로 Codex에 붙여 넣어도 이해하고 동작할 수 있게 쓰는 것을 권장합니다. 특히 첫 실행은 아래처럼 명시적으로 skill 이름을 불러 주는 편이 가장 안정적입니다.

### bootstrap

```text
Use $ralph-bootstrap to initialize this repository for Codex Ralph loop.
```

### PRD와 task 생성

```text
Use $ralph-prd to turn these requirements into .codex-loop/prd/PRD.md and .codex-loop/tasks.json.

Requirements:
- ...
- ...
```

### loop 실행

```text
Use $codex-ralph-loop to run the project-local Ralph loop from the current PRD and task files.
```

### 한 번에 시작

```text
Use $ralph-bootstrap to initialize this repository for Codex Ralph loop.
Then use $ralph-prd to convert my requirements into .codex-loop/prd/PRD.md and .codex-loop/tasks.json.
After that, review the generated task breakdown with me before running the loop.
```

slash command가 surface에 노출되는 환경이라면 아래도 사용할 수 있습니다.

```text
/init-codex-ralph
/run-codex-ralph
```

## Hook-native Ralph

이 플러그인은 이제 `./ralph.sh` 말고도 `Stop` hook 기반의 same-session Ralph를 지원합니다.

시작:

```text
/ralph-loop "Build the first vertical slice. Emit <promise>COMPLETE</promise> when truly done." --completion-promise "<promise>COMPLETE</promise>" --max-iterations 20
```

취소:

```text
/cancel-ralph
```

구조는 이렇습니다.

- 설치기가 전역 `~/.codex/hooks.json`에 dispatcher를 심음
- bootstrap된 repo는 `.codex-loop/ralph-loop.json`에 현재 Ralph 상태를 저장함
- `Stop` hook이 종료 시도를 continuation prompt로 바꿔 다시 먹임
- iteration limit, completion promise, blocked/decide promise는 state와 hook script가 관리함

## 프로젝트를 bootstrap 하면

대상 저장소에서 아래 명령을 실행하면:

```bash
python3 ~/.codex/plugins/codex-ralph-loop/scripts/bootstrap_project.py .
```

프로젝트 안에 아래가 생성됩니다.

- PRD, tasks, steering notes, logs, state를 담는 `.codex-loop/`
- loop engine인 `scripts/codex_ralph.py`
- 기획 문서 보조 도구인 `scripts/import_hwpx_preview.py`
- 실행 진입점인 `ralph.sh`
- loop 산출물을 위한 `.gitignore` 항목

이 시점부터 그 프로젝트는 loop-aware 상태가 됩니다. 플러그인은 재사용 가능하지만, runtime state는 그 저장소 소유가 됩니다.

## 전체 흐름

전체 경로를 요약하면:

1. plugin repo를 GitHub에 올림
2. 로컬에 clone
3. Codex에 plugin 설치
4. 필요하면 Codex 재시작
5. 대상 프로젝트 bootstrap
6. PRD와 task 파일 작성
7. `./ralph.sh` 실행

이게 실제 plugin experience입니다.

- plugin 설치로 skills 사용 가능
- bootstrap으로 repo를 runnable 상태로 만듦
- `ralph.sh`가 프로젝트별 loop를 실행

## 이 플러그인이 지향하는 감각

이 플러그인은 단순히 "스크립트 하나 실행"하는 느낌보다, Codex 안에서 자연스럽게 skill bundle이 붙는 느낌을 목표로 합니다.

- `skills/`는 역할별로 나뉘어 있어서 Codex가 metadata를 통해 찾기 쉽습니다.
- `chainTo` 규칙은 planning 작업에서 design/runtime guidance를 이어 붙일 수 있게 합니다.
- `commands/`는 사용자가 명시적으로 진입할 수 있는 entry point를 제공합니다.
- `personal-skills/`는 `~/.agents/skills`에 개인 취향을 오버레이할 수 있습니다.
- `hooks.json`은 핵심 제어 로직이 아니라, Bash 실행 후 주는 가벼운 리마인더입니다.

이상적인 흐름은 이렇습니다.

- plugin은 한 번만 설치
- 필요하면 개인용 overlay skill도 같이 설치
- 원하는 repo를 bootstrap
- 이후에는 프롬프트와 파일 상태를 보고 Codex가 맞는 loop skill을 집어듦
