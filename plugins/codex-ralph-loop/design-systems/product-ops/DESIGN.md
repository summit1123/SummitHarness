# Summit Product Ops

This preset is for operator-facing product UI, dashboards, tools, control
surfaces, and AI workflow consoles.

Preset: product-ops

## Intent

Ship interfaces that feel like real software used by accountable teams, not
generic AI app scaffolds.

## Principles

1. Workflow before polish
- The primary flow must be explicit before visual polish begins.
- Empty, loading, success, warning, and failure states are part of the product.

2. Structured density
- Use persistent layout regions, stable tables, logs, panels, and inspectors.
- Avoid floating marketing sections inside operational UI.

3. Evidence-rich UI
- Logs, state, provenance, approval status, and comparison views must look deliberate.
- A tool UI should expose state and decisions, not just pretty surfaces.

4. Asset discipline
- Every illustration, screenshot, or diagram must explain behavior or trust.
- Decorative assets are opt-in and rare.

5. Calm authority
- Strong type hierarchy, tight spacing, thin borders, and restrained accent use.
- Design should feel trustworthy, not energetic for its own sake.

## Layout Guidance

- Prefer split panes, data tables, timelines, logs, inspectors, and board-like surfaces.
- Use cards only when the box boundary is semantically meaningful.
- Keep visual grouping obvious through spacing and alignment before borders.

## Tone

- Operational, precise, and low-drama.
- Avoid anthropomorphic AI copy and product-marketing filler.

## Avoid

- dashboard confetti
- bento overload
- fake analytics tiles with no decisions attached
- ornamental gradients
- large empty hero zones in a tool
- assistant-style microcopy that describes the UI instead of the job

## Render Preference

- Source of truth: DESIGN.md + screen specs + approved assets
- Review gate: screenshot review and flow review
- Final artifact: implemented UI or annotated screen spec package
