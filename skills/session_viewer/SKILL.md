---
name: session_viewer
description: >
  OPTIONAL ops/debug skill (not in ship_skills). Render session transcripts
  (JSONL/text) as local HTML. Not a ship FSM step.
disable-model-invocation: true
user-invocable: true
max-retries: 0
timeout-seconds: 300
---

# Anti-patterns: policy/AGENT_REFERENCE.md · base_constraints
# `/session_viewer` — optional local session HTML (demoted; not ship_skills)

Use when the user wants to **view or export** a coding-agent session.

## Workflow

1. Locate session file (user path, or common locations under `~/.grok/`, `~/.claude/`,
   project `.agents/traces/`). Prefer user-provided path.
2. Render with the portable helper:

   ```bash
   python3 scripts/session_viewer.py /path/to/session.jsonl --out /tmp/session.html
   ```

3. Tell the user the HTML path. Do not upload or put raw secrets into PRs.
4. For GitHub PR bodies with sanitized history, use `/agent_transcript` instead.

## Handoff

```text
NEXT_SKILL=(return to ship path)
```

Resume ship with `python3 scripts/next_skill.py --after execute_dev` or the step you left.
