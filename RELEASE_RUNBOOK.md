# RELEASE_RUNBOOK — agent-harness v1.4.12

**Scope:** P0–P1 feedback loops (A1/A3, A5/A8, A4, A2/B6)  
**Score:** 100  
**Spec:** `.agents/specs/2026-08-02-p0-p1-feedback-loops.md`

## Evidence pack
| Item | Result |
|------|--------|
| hard_gates | ok |
| unittest | finish_ship, promote, portfolio, remaining |
| validate full | 5/5 |
| product_smoke | 2/2 |

## Smoke
| Step | Exit |
|------|------|
| hardcodes | 0 |
| unit | 0 |

## Things that look bad but are actually fine
1. finish_ship does not auto-run LLM skills
2. portfolio --push is opt-in
3. promote stubs are optional

## Rollback
`git checkout v1.4.11`
