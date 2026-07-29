# Ticket 01 — B1 Spec gate + B2 Traceability (P0)

**Status:** open  
**Blocked by:** none  
**Spec:** `.agents/specs/2026-07-29-adslc-a3-a5-layer-b-c.md`

## Goal

Code ships require linked spec (or waiver) before/during execute_dev, and AC→test/smoke mapping in PR_DRAFT enforced by hard_gates.

## Acceptance

- [ ] `scripts/spec_gate.py` exits 0/1  
- [ ] execute_dev skill documents pre-check  
- [ ] hard_gates requires Traceability section for non-prose  
- [ ] PR_DRAFT template updated  
- [ ] tests green  

## Smoke

`python3 scripts/hard_gates.py`; `pytest tests/test_hard_gates.py tests/test_spec_gate.py`
