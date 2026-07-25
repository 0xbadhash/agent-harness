---
name: agent_transcript
description: >
  Best-effort sanitized session summary for optional GitHub PR/issue bodies.
  Local-only discovery; always ask user before inserting; fail closed on secrets.
disable-model-invocation: true
user-invocable: true
max-retries: 0
timeout-seconds: 300
---

# `/agent_transcript` — sanitized PR provenance (P3)

Use during agent-created **GitHub PR/issue** workflows when the user wants a
collapsed transcript section.

## Contract

1. Prefer **local** session files only (no network scrape of secrets).
2. **Always ask** before adding anything to a PR/issue body.
3. Offer local preview (HTML via `/session_viewer` or markdown file) first.
4. **Fail closed** on unresolved secrets, keys, cookies, auth URLs, env dumps.
5. Drop system prompts, raw tool dumps, reasoning blocks, tokens, broad home paths.
6. Keep: user prompts, visible decisions, terse tool names, test/proof outcomes.
7. Trim to work **related to this PR/branch/goal** only.
8. If nothing safe found → continue PR without a transcript section (no placeholder).
9. Insert as collapsed `<details>` under `## Agent Transcript`; update markers, don’t duplicate.

## Helper

```bash
python3 scripts/agent_transcript.py find --query "…" --cwd . --since-days 14
python3 scripts/agent_transcript.py render --session /path/to/log --out /tmp/transcript.md
```

## Handoff

```text
NEXT_SKILL=(return to ship path)
```
