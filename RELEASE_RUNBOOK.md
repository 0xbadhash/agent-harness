# RELEASE RUNBOOK — agent-harness v1.3.1

**Date:** 2026-07-18  
**Tag:** v1.3.1  
**Scope:** night_shift multi-product dev env preflight (`ensure_product_dev_env.py`)

## Smoke
| Step | Result |
|------|--------|
| hardcodes | ✅ |
| unit | ✅ |
| validate full | ✅ |

## Rollback
`git checkout v1.3.0`

## §9
1. Preflight may pip install — local .venv only.  
2. No product auto-fix.  
3. Skip without requirements-dev is intentional.  
