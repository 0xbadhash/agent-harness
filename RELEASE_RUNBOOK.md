# RELEASE_RUNBOOK — agent-harness v1.4.29

**Score:** 100 · **Phase:** shipped · **2026-08-15**

## Smoke
| Step | Result |
|------|--------|
| hardcodes | pass |
| unit | pass |
| verify_skills | 14 ship skills |

## Rollback
`git checkout v1.4.28`

## §9
1. Optional skills still under skills/ on purpose  
2. Products need --delete-stale-skills  
3. audit_harness larger after merge  
