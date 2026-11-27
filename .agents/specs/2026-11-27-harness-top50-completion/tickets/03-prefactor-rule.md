# 03 — Prefactor ticket rule

**What to build:** Tickets declare a kind and a prefactor, and the DAG check fails
when a shared-component ticket has no prefactor predecessor.

**Kind:** feature
**Prefactor:** none
**Blocked by:** 01
**Estimate:** 140
**Status:** ready-for-agent

- [ ] Ticket template carries `**Kind:**` and `**Prefactor:**`
- [ ] `check_ticket_dag.py` fails when `Kind: shared-component` has no prefactor
      edge or a prefactor edge that does not exist
- [ ] `stack_plan.py` orders the prefactor before its dependent
- [ ] `pytest tests/test_decisions_and_review.py -q` covers the failure and pass cases
