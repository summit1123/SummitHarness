---
name: summit-visual-pipeline
description: 화면을 다듬기 전에 시각 방향, 승인된 에셋, Figma 기반 구현 입력을 정리합니다.
---

# Summit Visual Pipeline

Use this skill when design quality matters and raw JSX generation is not enough.

## Workflow

1. Define the visual direction before implementing UI details.
2. Generate or collect image/video/reference assets when text-only direction is too weak.
3. Register approved assets in `.codex-loop/assets/registry.json` with `python3 scripts/asset_registry.py add ...`.
4. When exact fidelity matters, use Figma as the source of truth and implement from there.
5. Feed the approved direction back into the compressed context packet before the next implementation pass.
