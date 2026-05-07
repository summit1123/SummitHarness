# /ralph-stage-gate

Evaluate a machine-readable SummitHarness stage artifact.

## Usage

```bash
python3 scripts/ralph_stage_gate.py init
python3 scripts/ralph_stage_gate.py checkpoint --stage research --requirement "Research must support the approved direction."
python3 scripts/ralph_stage_gate.py evaluate --stage research --artifact .codex-loop/stage-gates/artifacts/research.json
python3 scripts/ralph_stage_gate.py status
```

## Contract

Stage artifacts are JSON files under `.codex-loop/stage-gates/artifacts/`.

Every gate checks:

- Requirement mapping coverage is 100%
- Each core decision has evidence
- Critical/high issues are zero
- Stage score meets threshold
- Medium issues stay under the stage allowance and are recorded as residual risk
- Required user approval, test failure, evidence-free decisions, or missing requirements hard fail regardless of score

After two failed retries the gate returns a rollback target such as `research`, `r-and-d`, `interview_or_seed_prd`, or `user_judgment_gate`.

Prefer `checkpoint` during normal use. It creates the artifact from the current `.codex-loop` stage files and immediately evaluates it. Use `evaluate` when a worker has already produced a custom artifact JSON.
