---
name: gpa_eval
description: >
  Score a GPA trace on six 0-1 metrics, localize one error, and give one suggestion.
  Deterministic rubric in references/rubric.json. No LLM judge.
disable-model-invocation: true
user-invocable: true
max-retries: 0
timeout-seconds: 120
---

# gpa_eval

Input: a trace JSON from `gpa_trace`. Output: scores JSON.

```bash
python3 scripts/gpa_eval.py --trace TRACE.json --out SCORE.json
```

Metrics, each 0 to 1, all rubric (no LLM):

- outcome_correctness
- tool_selection
- tool_execution
- logical_consistency
- groundedness
- policy_adherence

Also `error_localization` (`step_index`, `why`) and exactly one `suggestion`.
Extends audit_harness evidence rules: cite the scorecard path, do not invent a second judge.
