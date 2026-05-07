# Ralph Quickstart

This is the shortest path for a new public all-rounder Ralph project.

## 1. Install

```bash
git clone https://github.com/summit1123/SummitHarness.git
cd SummitHarness
python3 install.py
```

Restart Codex after installation if commands or skills do not appear.

The installer registers the plugin and also links public skills such as `ralph-start`, `summit-start`, and `ralph-runtime` into `~/.codex/skills` so plain text like `ralph start` can route without requiring a slash command first.

## 2. Bootstrap A Project

From the target project:

```bash
python3 ~/.codex/plugins/codex-ralph-loop/scripts/bootstrap_project.py .
python3 scripts/preflight.py run
```

## 3. Start Onboarding

In Codex, prefer:

```text
ralph start
```

or:

```text
/ralph start
```

The start step is not a build loop. It chooses the workflow profile and captures what the user wants to do in this run.

## 4. Lock Inputs

Fill and approve:

- `.codex-loop/workflow/ONBOARDING.md`
- `.codex-loop/intake/ANSWERS.md`
- `.codex-loop/intake/APPROVAL.md`
- `.codex-loop/research/PLAN.md`
- `.codex-loop/research/FINDINGS.md`
- `.codex-loop/research/APPROVAL.md`

Approval must be explicit. Draft approval files do not count.

## 5. Run Stage Gates

```bash
python3 scripts/ralph_stage_gate.py orchestrate --start onboarding --end r-and-d --requirement "The approved user goal must be satisfied with mapped evidence."
```

For a release-readiness verification after implementation and evaluation evidence exists, run through the full public path:

```bash
python3 scripts/ralph_stage_gate.py orchestrate --start onboarding --end eval --requirement "The approved user goal must be satisfied with mapped evidence."
```

If a stage fails, Ralph writes:

- `.codex-loop/stage-gates/orchestration/latest.json`
- `.codex-loop/stage-gates/results/<stage>-latest.json`
- `.codex-loop/stage-gates/remediation/<stage>-latest.json`
- `.codex-loop/tasks/TASK-SG-*.json`

The remediation task is promoted to `in_progress` unless the next action requires user judgment.

## 6. Run Ralph

```bash
./ralph.sh
```

By default, project-local Ralph checks stage gates before worker execution. If gates fail, worker execution is blocked and remediation is required first.
