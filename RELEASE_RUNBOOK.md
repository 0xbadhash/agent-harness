# RELEASE_RUNBOOK — agent-harness v1.4.14

**Scope:** detailed ship-flow docs (Mermaid + Draw.io/SVG) for operators + LLMs  
**Score:** 100  
**Spec waiver:** docs-only

## Evidence pack
| Item | Result |
|------|--------|
| hard_gates | ok |
| validate full | 5/5 |
| product_smoke | 2/2 |
| remote | tag v1.4.14 + ship-flow-detailed.md |

## Smoke
| Step | Exit |
|------|------|
| hardcodes | 0 |
| unit | 0 |

## Things that look bad but are actually fine
1. Docs tagged before this formal FSM closeout in-session
2. SVG hand-authored alongside Draw.io
3. Portfolio reinstall still run for doc install path

## Rollback
`git checkout v1.4.13`
