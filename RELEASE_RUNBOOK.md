# RELEASE_RUNBOOK — agent-harness v1.4.8

**Scope:** ADSLC harden ticket 01 (A3 daytime ops)  
**Score:** 100  
**Spec:** `.agents/specs/2026-07-29-adslc-a3-b5-c5-harden.md`

## Evidence pack
| Item | Result |
|------|--------|
| hard_gates | ok |
| unittest | test_daytime_wiring 4 OK |
| validate full | 5/5 |
| product_smoke | 2/2 |
| wiring | check_daytime_wiring ok |

## Smoke
| Step | Exit |
|------|------|
| hardcodes | 0 |
| unit (smoke_unit.sh) | 0 |

## Things that look bad but are actually fine
1. Deploy unit host paths match night-shift-all
2. Timer not auto-enabled
3. start_feature ruff fix in same commit

## Rollback
`git checkout v1.4.7`
