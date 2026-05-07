# Stage Artifact Schemas

Every stage artifact is a JSON object. The gate currently enforces this common shape and adds stage-specific quality checks.

## Common Fields

- `stage`: one of `onboarding`, `interview`, `seed-prd`, `research`, `design`, `r-and-d`, `dev`, `eval`
- `requirementMapping`: non-empty array, every item must map a requirement to at least one evidence id
- `evidence`: non-empty array of concrete file, directory, source, visual, test, or evaluation evidence
- `coreDecisions`: non-empty array, every decision must reference at least one known evidence id
- `score`: numeric automatic or custom score
- `issues`: array of `critical`, `high`, `medium`, or `low` issues
- `residualRisks`: required when any accepted medium issue remains
- `approval`: `{ "required": boolean, "granted": boolean }`
- `checks`: stage-specific machine checks such as passing tests

## Research

Research must include concrete source/evidence markers in `.codex-loop/research/FINDINGS.md`, and the plan must be detailed enough to support deep research. Core claims without evidence should fail before design or implementation.

## Design

Design must select a `Reference-Pack` in `.codex-loop/design/DESIGN.md` and should attach visual output, screenshots, or registered assets. A design gate without inspectable output is only a draft.

## R&D

R&D must show feasibility, spike, prototype, tradeoff, risk, or experiment evidence. It is not a second PRD; it exists to reduce implementation uncertainty.

## Dev

Dev must record a passing local test, build, or smoke result through `.codex-loop/state.json`. Without a passing check, dev does not pass even if files changed.

## Eval

Eval must record passing goal evaluation and leave review/eval artifacts. Task completion alone is not sufficient.

