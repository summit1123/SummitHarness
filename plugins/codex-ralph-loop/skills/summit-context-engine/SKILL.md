---
name: summit-context-engine
description: Use when a long-running Codex task needs compressed handoff packets, durable facts, open questions, or context refreshes instead of replaying the entire transcript.
---

# Summit Context Engine

Use this skill when the user wants the harness to remember what matters without stuffing the whole raw history back into the next turn.

## Workflow

1. Treat `.codex-loop/context/` as the compressed working memory layer.
2. Refresh the packet with `python3 scripts/context_engine.py refresh --source <reason>` whenever the repo state materially changes.
3. Put long-lived facts into `durable.json` and unresolved questions into `open-questions.json`.
4. Prefer replaying `handoff.md` over replaying the full raw transcript.
5. Keep the compressed packet short, actionable, and tied to the actual repo state.
