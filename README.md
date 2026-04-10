# SummitHarness

`SummitHarness` packages a Codex-native Ralph loop as a reusable plugin bundle.

It is meant to cover two layers at once:

- a public plugin that anyone can install into Codex
- optional personal overlay skills that stay specific to your own working style

## Repo layout

```text
SummitHarness/
├── .agents/plugins/marketplace.json
├── plugins/codex-ralph-loop/
├── personal-skills/
├── install.py
└── install.sh
```

## What the plugin contains

The distributable plugin lives at
[`plugins/codex-ralph-loop/`](./plugins/codex-ralph-loop/README.md).

That bundle includes:

- bundled `skills/` for PRD work, runtime loop execution, design gates, and review gates
- `commands/` for explicit entry points
- `templates/project/` for seeding a target repository
- installer and bootstrap scripts
- plugin assets and lightweight hook wiring

## What deployment means

For this repo, deployment means publishing the source to GitHub so another user
can:

1. clone the repository
2. run the installer
3. restart Codex
4. bootstrap a target project
5. run `./ralph.sh`

This is a plugin-source repository, not an npm package. An npm wrapper could be
added later, but the installable artifact is still the plugin directory.

## Install for Codex

From the cloned repository root:

```bash
python3 install.py
```

That does three things:

1. copies `plugins/codex-ralph-loop/` into `~/.codex/plugins/codex-ralph-loop`
2. updates `~/.agents/plugins/marketplace.json`
3. symlinks or copies any valid skills in `personal-skills/` into `~/.agents/skills/`

If you want only the public plugin and no personal overlays:

```bash
python3 install.py --no-personal-skills
```

If Codex does not show the plugin or skills immediately, restart Codex.

## What happens after install

After install, Codex can discover:

- the plugin manifest
- the bundled plugin skills
- the plugin commands
- any user-specific skills installed from `personal-skills/`

The plugin does not automatically start a loop. Install only makes the workflow
available to Codex.

## Bootstrap a target project

Inside any target repository:

```bash
python3 ~/.codex/plugins/codex-ralph-loop/scripts/bootstrap_project.py .
```

That creates:

- `.codex-loop/` for PRD, tasks, steering notes, logs, and state
- `scripts/codex_ralph.py`
- `scripts/import_hwpx_preview.py`
- `ralph.sh`
- loop-related `.gitignore` entries

Then fill in the PRD and tasks and run:

```bash
./ralph.sh --once
```

## Repo-local development

This repository also includes
[`/.agents/plugins/marketplace.json`](./.agents/plugins/marketplace.json), so
if you open `SummitHarness` itself in Codex, the repo-local plugin can be
discovered without first installing it home-locally.

## Personal overlays

The public plugin should stay generally useful. Anything that is too specific to
your own taste or workflow belongs under
[`personal-skills/`](./personal-skills/README.md).

Examples:

- stricter review rules
- stronger product taste
- your preferred architecture defaults
- custom escalation rules

Those skills are not part of the public plugin contract. They are user-specific
overlays installed into `~/.agents/skills/`.

## References

- [Codex plugins](https://developers.openai.com/codex/plugins/build)
- [Codex skills](https://developers.openai.com/codex/skills)
- [Codex hooks](https://developers.openai.com/codex/hooks)
