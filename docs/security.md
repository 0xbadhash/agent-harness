# Security

## This harness

- No secrets in repo  
- Smoke commands are argv lists (prefer no `shell=True` in product plugins)  
- Vault scripts must not log env secrets  
- `pr_validator` / compliance run local tools only  

## Third-party skills

Community skill indexes are high-risk.

**Before installing any external `SKILL.md` into a product:**

1. Read the full body  
2. Read any `scripts/` it runs  
3. Prefer known authors / high use  
4. Test on a disposable project first  
5. Never paste API keys into skill files  

Treat skills like executable policy—same hygiene as dependencies.

## Product infra skills

Deploy/topology skills stay product-local. Do not merge production hostnames into this public harness.

## Related

- [Writing skills](writing-skills.md)  
