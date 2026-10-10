---
name: gpa_trace
description: >
  Emit a redacted Goal-Plan-Action trace JSON for a finished task.
  Use after Pilot brief execution, Hermes Signal/X send, Jobs apply, or Substack schedule.
  No new bot. Reuse agent_transcript and session_viewer for raw history; this skill only writes the trace.
disable-model-invocation: true
user-invocable: true
max-retries: 0
timeout-seconds: 120
---

# GPA trace fragment

Those four lanes are not separate skills in this repo. Attach this fragment when one of them finishes.

Write `agent-tasks/evals/traces/YYYY-MM-DD/<lane>-<task>.json` under the vault. Redact secrets, tokens, passwords, and cookies before write. Do not print them.

```json
{
  "goal": "",
  "expected": "",
  "plan": [{"index": 0, "step": ""}],
  "actions": [{"index": 0, "tool": "", "args_redacted": "", "result_summary": "", "ok": true}],
  "outcome": "",
  "policy_points": [{"rule": "", "honoured": true, "evidence": ""}],
  "scorecard_path": ""
}
```

Point `scorecard_path` at the evidence scorecard. Then run `python3 scripts/gpa_eval.py` on the trace.
