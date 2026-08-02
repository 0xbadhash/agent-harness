# RELEASE_RUNBOOK — agent-harness v1.4.13

**Scope:** P0 run_ship_chain + night_fail_remediate + default portfolio push  
**Score:** 100  
**Spec:** `.agents/specs/2026-08-02-p0-unattended-and-remediate.md`

## Evidence pack
| Item | Result |
|------|--------|
| hard_gates | ok |
| unittest | run_ship_chain + night_fail_remediate |
| validate | 5/5 |
| product_smoke | 2/2 |

## Smoke
| hardcodes | 0 |
| unit | 0 |

## Things that look bad but are actually fine
1. No LLM auto slash skills
2. Portfolio push on harness release only
3. Remediaten does not invent product features

## Rollback
`git checkout v1.4.12`
