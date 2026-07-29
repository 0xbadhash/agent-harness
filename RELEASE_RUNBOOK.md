# RELEASE_RUNBOOK — agent-harness v1.4.9

**Scope:** ADSLC harden ticket 02 (B5 Evidence pack hard gate)  
**Score:** 100  
**Spec:** `.agents/specs/2026-07-29-adslc-a3-b5-c5-harden.md`

## Evidence pack
| Item | Result |
|------|--------|
| hard_gates | ok |
| unittest | test_hard_gates 9 OK |
| validate full | 5/5 |
| product_smoke | 2/2 |

## Smoke
| Step | Exit |
|------|------|
| hardcodes | 0 |
| unit | 0 |

## Things that look bad but are actually fine
1. ## Evidence vs ## Evidence pack are distinct sections
2. Token keywords not CI XML
3. Line-start match only for Evidence pack header

## Rollback
`git checkout v1.4.8`
