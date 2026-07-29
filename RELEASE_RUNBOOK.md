# RELEASE_RUNBOOK — agent-harness v1.4.6

**Scope:** ADSLC tickets 01–05 (A3–A5, Layer B, Layer C)  
**Score:** 100 (hard gates pack)

## Evidence pack
| Item | Result |
|------|--------|
| hard_gates | ok |
| pytest | 107+ |
| validate full | 5/5 |
| product_smoke | 2/2 |
| Spec | `.agents/specs/2026-07-29-adslc-a3-a5-layer-b-c.md` |

## Smoke
| Step | Exit |
|------|------|
| hardcodes | 0 |
| unit (smoke_unit.sh) | 0 |

## §9
1. Single release for five tickets  
2. delete-stale-skills only explicit removed list  
3. qa_campaign large-only by default  

## Rollback
`git checkout v1.4.5`
