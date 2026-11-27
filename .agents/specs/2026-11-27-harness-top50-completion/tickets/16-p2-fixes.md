# 16 — P2 follow-ups: estimate and ticket-root scan

**What to build:** Close the two P2 findings from the v1.4.57 review.

**Kind:** fix
**Prefactor:** none
**Blocked by:** None
**Estimate:** 90
**Status:** ready-for-agent

- [ ] `stack_plan.py` accepts `--default-estimate` and documents the fallback;
      per-ticket `**Estimate:**` still wins
- [ ] The CI ticket-DAG step finds every `tickets/` directory under `.agents/specs`
      and honors a configured product root
- [ ] `pytest tests/test_stack_runners.py -q` covers both
