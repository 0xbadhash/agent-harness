# 02 — Door-aware review tiers and feature-flag gate

**What to build:** Review depth keyed by the existing `**Door:**` field, and a
feature-flag requirement for user-visible large ships.

**Kind:** feature
**Prefactor:** none
**Blocked by:** 01
**Estimate:** 160
**Status:** ready-for-agent

- [ ] `pr_review` names a two-way tier (agent gates) and a one-way tier (human
      sign-off plus rollout and rollback lines)
- [ ] `spec_gate.py` reports a missing `**Door:**` and, for user-visible large
      ships, a missing `**Feature flag:**`; `--strict` fails
- [ ] `templates/PR_DRAFT.md` and the spec/plan templates carry the flag field
- [ ] `pytest tests/test_decisions_and_review.py -q` covers both tiers and the flag
