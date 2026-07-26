# RELEASE RUNBOOK — agent-harness v1.4.0

**Date:** 2026-07-26  
**Tag:** v1.4.0  

## Scope
Any-LLM bootstrap: install --verify, bootstrap_check, verify_skills ship-chain, llm-bootstrap docs, install tests.

## Smoke
| Step | Result |
|------|--------|
| run_harness_tests.sh | ✅ 7 unittest |
| verify_skills.py . | ✅ 19 skills, 13 ship |
| bootstrap_check.sh . | ✅ |

## Rollback
`git checkout v1.3.7`

## §9
1. Install does not delete product-only skills.  
2. product_plugin.yaml left as-is on re-install.  
3. Harness prefers skills/ SoT over stale .agents/skills when install script present.  
4. pytest optional.  
5. No vault required.  
