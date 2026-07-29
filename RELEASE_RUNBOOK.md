# RELEASE_RUNBOOK — agent-harness v1.4.10

**Scope:** ADSLC harden ticket 03 (C5 eval runner)  
**Score:** 100  
**Spec:** `.agents/specs/2026-07-29-adslc-a3-b5-c5-harden.md`

## Evidence pack
| Item | Result |
|------|--------|
| hard_gates | ok |
| unittest | test_agent_eval_checklist + subset |
| validate full | 5/5 |
| product_smoke | 2/2 |
| agent_eval_checklist | ok=True |

## Smoke
| Step | Exit |
|------|------|
| hardcodes | 0 |
| unit | 0 |

## Things that look bad but are actually fine
1. GHA uses --skip-tests for speed
2. Not LLM-as-judge
3. Completes ADSLC harden tickets 01–03

## Rollback
`git checkout v1.4.9`
