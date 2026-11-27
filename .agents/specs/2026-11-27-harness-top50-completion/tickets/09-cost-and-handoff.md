# 09 — Session cost artifact and handoff token threshold

**What to build:** Token/context/cost reporting per ship and a token threshold
that triggers a clean-context handoff from execute_dev.

**Kind:** feature
**Prefactor:** none
**Blocked by:** 05
**Estimate:** 170
**Status:** ready-for-agent

- [ ] `session_context.py` writes `.agents/artifacts/SESSION_COST.md` with
      tokens, context, cost, or `unknown` when unavailable
- [ ] `handoff` defines a token threshold and `execute_dev` checks it before
      starting another ticket
- [ ] `pytest tests/test_prototype_and_handoff.py -q` covers known and unknown
      cost paths
