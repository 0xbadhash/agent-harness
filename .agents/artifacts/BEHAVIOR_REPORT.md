# BEHAVIOR-REPORT

**Marker:** BEHAVIOR-REPORT  
**Runtime surface:** CLI scripts (ops_dashboard, night_shift_log, test_trigger_schedule)

## Contract
Operators can read **when tests run** from OPS-DASHBOARD and product night-shift-log without opening harness source.

## Clauses

| ID | Clause | Result | Evidence |
|----|--------|--------|----------|
| B1 | `python3 scripts/test_trigger_schedule.py` prints ship + night + daytime rows | **pass** | CLI output includes `/pr_review`, Night shift, daytime-gates |
| B2 | `ops_dashboard.py --write` includes “When tests run (act map)” | **pass** | Vault OPS-DASHBOARD section present after write |
| B3 | Rewritten `night-shift-log.md` includes schedule block | **pass** | email-detach / watchlist logs contain “When tests run” |
| B4 | Invalid/missing import does not crash dashboard write | **pass** | try/except around schedule import in ops_dashboard |

## Anti-cheat
- Empty vault path still skips vault; schedule still attempts embed from harness scripts.
- Schedule is static data — not derived from live CI (documented).

## Verdict
Behavior matches ops documentation intent. Safe for `/pr_review --validate`.

NEXT_SKILL=/pr_review --validate
