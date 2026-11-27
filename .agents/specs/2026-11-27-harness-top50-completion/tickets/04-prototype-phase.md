# 04 — Prototype phase and fidelity check

**What to build:** A prototype skill that wraps the disposable-variant generator,
prototype fields in the spec and PR draft, and a merge-time fidelity check.

**Kind:** feature
**Prefactor:** none
**Blocked by:** 01
**Estimate:** 200
**Status:** ready-for-agent

- [ ] `skills/prototype/SKILL.md` explains new/list/choose/delete and the
      "reference, never implementation" rule
- [ ] Spec and `templates/PR_DRAFT.md` carry `**Prototype:**` and
      `**Prototype verdict:**`
- [ ] `scripts/check_prototype_fidelity.py` fails when the chosen variant still
      exists, when the PR lacks a verdict, or when implementation code is marked
      as copied from a prototype
- [ ] `pytest tests/test_prototype_and_handoff.py -q` covers pass and fail cases
