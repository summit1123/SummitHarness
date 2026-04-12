---
name: summit-visual-pipeline
description: Use when the harness should establish an actual visual direction, approved assets, or Figma-backed implementation inputs before polishing UI code.
---

# Summit Visual Pipeline

Use this skill when design quality matters and raw JSX generation is not enough.

## Workflow

1. Define the visual direction before implementing UI details.
2. Generate or collect image/video/reference assets when text-only direction is too weak.
3. Register approved assets in `.codex-loop/assets/registry.json` with `python3 scripts/asset_registry.py add ...`.
4. When exact fidelity matters, use Figma as the source of truth and implement from there.
5. Feed the approved direction back into the compressed context packet before the next implementation pass.
