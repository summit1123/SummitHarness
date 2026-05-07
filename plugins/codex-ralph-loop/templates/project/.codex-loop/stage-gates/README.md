# Stage Gates

`ralph_stage_gate.py` evaluates the public all-rounder Ralph flow with machine-readable artifacts.

See `SCHEMAS.md` for the common artifact contract and stage-specific quality checks.

Every stage artifact must be JSON and must include:

- `stage`: one of `onboarding`, `interview`, `seed-prd`, `research`, `design`, `r-and-d`, `dev`, `eval`
- `requirementMapping`: every known requirement with at least one evidence id
- `evidence`: concrete source, file, log, reference, image, or generated asset evidence
- `coreDecisions`: decisions with evidence ids
- `score`: automatic evaluation score
- `issues`: critical/high/medium/low findings
- `residualRisks`: required whenever a medium issue is accepted
- `checks.tests.passed`: required for dev/eval artifacts that claim test success

Common pass rules:

- Requirement mapping coverage is `100%`
- Every core claim and core decision has at least one evidence item
- Critical and high issues are `0`
- Research/design/R&D score is at least `0.85`
- Dev/eval score is at least `0.90`
- Medium issues are capped by stage and must be recorded in residual risks

Hard fails ignore score:

- Missing required user approval
- Test failure
- Evidence-free core decision
- Missing requirement mapping

Run:

```bash
python3 scripts/ralph_stage_gate.py init
python3 scripts/ralph_stage_gate.py orchestrate --start onboarding --end eval --requirement "The run must satisfy the approved user goal."
python3 scripts/ralph_stage_gate.py checkpoint --stage research --requirement "Research must support the approved direction."
python3 scripts/ralph_stage_gate.py evaluate --stage research --artifact .codex-loop/stage-gates/artifacts/research.json
python3 scripts/ralph_stage_gate.py status
```

`orchestrate` is the happy path for normal Ralph runs: it runs stage checkpoints in order, stops at the first failed gate, writes `.codex-loop/stage-gates/orchestration/latest.json`, creates a `.codex-loop/tasks/TASK-SG-*.json` remediation task, and records whether the next move is remediation, rollback, or a user judgment gate. `checkpoint` is useful when you only want to evaluate one stage.
