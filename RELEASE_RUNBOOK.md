# Release runbook — agent-harness v1.3.4

**Date:** 2026-07-25  
**Scope:** Review closeout improvements (scope, P0, code_review, secrets, prose skip)

## Smoke

| Check | Result |
|-------|--------|
| unittest review_scope + secrets | PASS |
| validate.py full | 5/5 |
| product_smoke | PASS |

## Rollback

```bash
git checkout v1.3.3
```

## §9

1. Skills need product reinstall to refresh product copies.  
2. gitleaks optional.  
3. No pipeline auto-advance from code_review.
