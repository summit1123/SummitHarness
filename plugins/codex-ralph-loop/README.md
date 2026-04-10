# Codex Ralph Loop Plugin

This plugin can be used two ways:

- repo-local, like this workspace
- home-local, as a reusable plugin anyone can install

What lives here:

- `skills/`: specialized skills for bootstrap, PRD work, runtime loops, design gates, and review gates
- `hooks.json`: lightweight Bash-tool reminder hook
- `assets/`: plugin identity
- `templates/project/`: runtime files that get seeded into a target repo
- `scripts/bootstrap_project.py`: seeds `.codex-loop/`, `ralph.sh`, and helper scripts
- `scripts/install_home_local.py`: copies this plugin to `~/.codex/plugins/codex-ralph-loop`, updates `~/.agents/plugins/marketplace.json`, and optionally links personal skills into `~/.agents/skills`

What lives outside:

- PRD
- task graph
- steering notes
- run logs
- history
- review outputs

The loop runner itself is shipped as a project template. After bootstrap, the
target project gets its own `scripts/codex_ralph.py` and `ralph.sh`.

## Portable install

From inside this plugin directory:

```bash
python3 scripts/install_home_local.py
```

Then in any target project:

```bash
python3 ~/.codex/plugins/codex-ralph-loop/scripts/bootstrap_project.py .
./ralph.sh --once
```

That is the piece that makes this a reusable plugin rather than a one-off repo
experiment.

## What deployment means

For this plugin, "deploy" usually means publishing the plugin source to a GitHub
repository so another developer can clone it or run an install script from it.

Typical distribution flow:

1. Push this plugin to its own repository, for example `SummitHarness`.
2. A user clones that repository locally.
3. The user runs the installer script from the cloned repo.
4. The installer copies the plugin into the user's Codex plugin area and updates
   the local plugin marketplace file.
5. Codex can then discover the plugin's bundled skills.

This is different from an npm package. npm can be added later as a wrapper, but
the core artifact is still the plugin folder itself.

## What happens during install

When a user runs the installer:

```bash
python3 scripts/install_home_local.py
```

the expected lifecycle is:

1. Copy `plugins/codex-ralph-loop/` into `~/.codex/plugins/codex-ralph-loop`.
2. Register that plugin in `~/.agents/plugins/marketplace.json`.
3. If `personal-skills/` exists in the source repo, symlink or copy those skills
   into `~/.agents/skills/`.
4. Restart Codex if the plugin does not appear immediately.

After that, Codex can see:

- the plugin manifest
- the bundled `skills/`
- the plugin `commands/`
- any plugin assets and helper scripts

The important part is that Codex does not "run the plugin" as one big program.
It discovers the bundled skills and then chooses those skills when the prompt,
workspace files, or explicit `$skill-name` mention matches them.

## What happens after install inside Codex

Once installed and visible to Codex:

1. The plugin's bundled skills become available for explicit use.
2. Those same skills can also be invoked implicitly when their descriptions and
   metadata match the user's task.
3. The commands can show up as slash-command style entry points depending on the
   Codex surface.
4. The plugin can guide workflow, but it still needs a target project to
   bootstrap before a loop can run.

So install alone does not start a Ralph loop. Install only makes the workflow
available to Codex.

## What happens when you bootstrap a project

Inside a target repository, this command:

```bash
python3 ~/.codex/plugins/codex-ralph-loop/scripts/bootstrap_project.py .
```

seeds the project with:

- `.codex-loop/` for PRD, tasks, steering notes, logs, and state
- `scripts/codex_ralph.py` as the loop engine
- `scripts/import_hwpx_preview.py` as a planning-doc helper
- `ralph.sh` as the user-facing entrypoint
- `.gitignore` additions for loop artifacts

At that point the project becomes loop-aware. The plugin stays reusable, but the
runtime state now belongs to that repository.

## End-to-end picture

The full path looks like this:

1. Publish plugin repo to GitHub
2. Clone repo locally
3. Install plugin into Codex
4. Restart Codex if needed
5. Bootstrap a target project
6. Fill in PRD and task files
7. Run `./ralph.sh`

That is the actual "plugin experience":

- plugin install makes skills available
- bootstrap makes a repo runnable
- `ralph.sh` runs the project-specific loop

## Plugin feel

This plugin is meant to feel more native than "run this script manually."

- `skills/` are split by role so Codex can discover them through metadata
- `chainTo` rules let planning work pull in design or runtime guidance
- `commands/` give the user explicit entry points
- `personal-skills/` can overlay your private preferences into `~/.agents/skills`
- `hooks.json` is a lightweight Bash completion nudge, not a core control path

So the ideal experience is:

- install plugin once
- optionally install personal overlay skills at the same time
- bootstrap any repo
- let Codex pick up the right loop skill based on the prompt and files
