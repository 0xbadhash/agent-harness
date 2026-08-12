# RELEASE_RUNBOOK — v1.4.27

**When:** 2026-08-12  
**Score:** 100 (pr_validator)  
**Phase:** approved → shipped

## Smoke

| Step | Result |
|------|--------|
| product_smoke | see release session log |
| validate full --skip-vault-schema | gates as run in session |
| pytest | 188 passed |

## Infra
N/A — agent-harness has no VPS install root gate for this release (docs/ops scripts only).

## Contents
- Test trigger schedule in OPS-DASHBOARD + night-shift-log
- SoT: scripts/test_trigger_schedule.py

## Rollback
```bash
git checkout v1.4.26
```

## Things that look bad but are actually fine
1. Spec waiver chore on closeout PR_DRAFT.
2. GitHub daytime still not scraped into OPS fail rows.
3. Vault schema lint may fail on unrelated catalyxt dirs — skipped with --skip-vault-schema for harness SoT.
4. Portfolio products may still show protect drift.
5. Night logs rewritten once; next night run refreshes with new report format.
