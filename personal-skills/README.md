# 개인용 스킬

이 디렉터리는 공개 플러그인 안에 넣기엔 너무 개인적인 기준을 담기 위한 공간입니다.

각 폴더는 일반적인 Codex skill 형태를 따르면 됩니다.

```text
personal-skills/
  my-skill/
    SKILL.md
```

`install_home_local.py`는 `--no-personal-skills` 옵션이 없는 한, 여기 있는 유효한 skill 폴더를 `~/.agents/skills/`로 symlink 또는 copy 합니다.

예를 들면 이런 용도로 씁니다.

- 본인만의 리뷰 엄격도
- 디자인 취향 메모
- 선호하는 코딩 패턴
- 공개 플러그인에 넣기엔 너무 개인적인 프로젝트 선택 기준
