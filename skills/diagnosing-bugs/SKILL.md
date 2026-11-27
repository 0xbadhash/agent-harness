---
name: diagnosing-bugs
description: >
  Disciplined 5-phase diagnosis loop for hard bugs and performance regressions:
  tight red-capable loop first, then minimise, hypothesise, instrument with
  [DEBUG-<id>] tags, and lock down with a seam-level regression test.
user-invocable: true
max-retries: 0
timeout-seconds: 900
---
# Anti-patterns: policy/AGENT_REFERENCE.md · base_constraints

1. **Build a tight red-capable loop first:** Name one fast, deterministic command that fails on the exact user symptom before reading code or hypothesising.
2. **Reproduce and minimise:** Strip non-load-bearing inputs/steps until every remaining piece is required to trigger the failure.
3. **Hypothesise (3-5 ranked, falsifiable):** State `"If <X> is the cause, then <Y> will change the verdict"` before probing.
4. **Instrument:** Tag temporary debug logs with `[DEBUG-<id>]` (e.g. `[DEBUG-a4f2]`); `scripts/check_repo_hygiene.py` fails closed if any `[DEBUG-` tag survives into commit.
5. **Fix + regression test:** Write the failing test at the true caller seam, apply the minimal fix, and remove all `[DEBUG-` instrumentation.
