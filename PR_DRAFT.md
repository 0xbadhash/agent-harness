# PR Draft — Hard gates pack

**Date:** 2026-07-29  
**Version:** 1.4.5  
**Spec:** `.agents/specs/2026-07-29-hard-gates-pack.md`  
**Plan:** `.agents/specs/2026-07-29-hard-gates-pack-plan.md`

## What Problem This Solves
Soft skill text allowed unreviewed code ships to score ≥95 without CODE-REVIEW, red-proof, behavior proof, or spec linkage.

## Why This Change Was Made
Fail-closed hard gates in `pr_validator` (25 pts) via `hard_gates.py` so the FSM delivers designed quality.

## User Impact
Operators/agents must produce evidence pack before approve; hotfixes use **Spec waiver**.

## Evidence
- tests/test_hard_gates.py (6 cases)
- scripts/hard_gates.py + pr_validator integration
- docs/ship-flow.md Hard gates section

## Red-proof
- red_cmd: `python3 -m unittest tests.test_hard_gates -v` (failed before implement)
- green_cmd: `python3 -m unittest tests.test_hard_gates -v` (6 OK after)

## Things that look bad but are actually fine
1. --skip-hard-gates exists for emergencies only  
2. Secrets skip when not a git root (unit fixtures)  
3. Behavior only when runtime surface  
4. Rubric rebalance still totals 100  
5. Spec waiver is intentional escape for hotfix/chore  

## Cross-review
Hard gates are small, focused module — personas optional; CODE-REVIEW present.
