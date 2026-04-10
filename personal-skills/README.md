# Personal Skills

This directory is for user-specific overlays that should not live inside the
shared plugin itself.

Each folder here should be a normal Codex skill:

```text
personal-skills/
  my-skill/
    SKILL.md
```

`install_home_local.py` will install or symlink any valid skill folders here
into `~/.agents/skills/` unless `--no-personal-skills` is used.

Use this for:

- your own review strictness
- design taste notes
- preferred coding patterns
- project selection heuristics that are too personal for the public plugin
