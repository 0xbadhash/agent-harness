# RELEASE_RUNBOOK — agent-harness v1.4.2

**Scope:** night_shift P0–P2 (hardcodes, vault normalize/ACL, daytime gates)  
**Infra:** N/A  
**Smoke:** hardcodes + unit pass; validate 5/5  

## §9
1. content/vault skip is intentional for product trees  
2. daytime subset is optional ops, not timer replacement  
3. second-brain path portability is companion product commit  

## Rollback
`git checkout v1.4.1`
