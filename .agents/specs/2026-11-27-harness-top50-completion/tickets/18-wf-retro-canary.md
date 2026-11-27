# 18 — workflow-harness run-record retro and canary gate

**What to build:** Analyze run records for status, attempts, tokens, and cost,
and gate workflow step changes behind a canary comparison.

**Kind:** feature
**Prefactor:** none
**Blocked by:** 17
**Estimate:** 170
**Status:** ready-for-agent

- [ ] `scripts/retro_runs.py` summarizes runs and flags repeated failures
- [ ] `scripts/check_canary.py` requires a canary field and a comparison note on
      workflow step changes
- [ ] The workflow-harness test suite covers pass and fail paths
