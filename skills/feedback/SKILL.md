---
name: feedback
description: Append end-of-session notes to .agents/AGENT_FEEDBACK.md (harness only).
disable-model-invocation: true
user-invocable: true
max-retries: 0
timeout-seconds: 120
preserve-artifacts-on-failure: true
---
# Reads: .agents/AGENT_FEEDBACK.md, .agents/AGENT_WORKFLOW.md
# Writes: .agents/AGENT_FEEDBACK.md (prepend entry)
# Anti-patterns: docs/AGENT_REFERENCE.md
# Not product: feedback is meta; product backlog is BACKEND_ROADMAP.md

When invoked with `/feedback`:
1. Summarize the session (task, outcome, friction, harness gap, follow-up).
2. Prepend a dated section to `.agents/AGENT_FEEDBACK.md` (newest first).
3. Never write secrets, tokens, or `.env` values.
4. Optional: one-line vault note if **product** work shipped (see root `AGENTS.md`).
5. Output: `✅ FEEDBACK LOGGED` + path.

Does **not** change `pipeline.json`.
