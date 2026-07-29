# RELEASE_RUNBOOK — agent-harness v1.4.5

**Scope:** Hard gates pack for pr_validator  
**Score:** 100  
**Infra:** N/A  

## Smoke
| Step | Result |
|------|--------|
| hardcodes | pass |
| unit | pass |
| validate full | 5/5 |
| hard_gates | ok |

## §9
1. --skip-hard-gates is emergency only  
2. Prose-only skips CODE-REVIEW/red-proof/behavior  
3. Spec waiver is intentional for hotfix/chore  

## Rollback
`git checkout v1.4.4`
