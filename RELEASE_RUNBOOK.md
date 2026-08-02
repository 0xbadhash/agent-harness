# RELEASE_RUNBOOK — agent-harness v1.4.11

**Scope:** night_shift morning triage (feedback loop slice 1)  
**Score:** 100  
**Spec:** `.agents/specs/2026-08-02-night-shift-morning-triage.md`

## Evidence pack
| Item | Result |
|------|--------|
| hard_gates | ok |
| unittest | morning_triage 4 OK |
| validate full | 5/5 |
| product_smoke | 2/2 |

## Smoke
| Step | Exit |
|------|------|
| hardcodes | 0 |
| unit | 0 |

## Things that look bad but are actually fine
1. Exit 1 when products FAIL is intentional
2. No auto-ship of TODOs
3. Timer opt-in via --apply

## Rollback
`git checkout v1.4.10`
