# RELEASE_RUNBOOK — agent-harness v1.4.15

**Scope:** CODER P2–P3 (session_context, mode labels, prompt-patterns)  
**Score:** 100  
**Spec waiver:** docs-only

## Evidence pack
| Item | Result |
|------|--------|
| hard_gates | ok |
| unittest | test_session_context 2 OK |
| validate | 5/5 |
| product_smoke | 2/2 |

## Smoke
| hardcodes | 0 |
| unit | 0 |

## Things that look bad but are actually fine
1. CODER is teaching overlay not FSM
2. Prompt pattern names informal
3. session_context may show product night FAILs

## Rollback
`git checkout v1.4.14`
