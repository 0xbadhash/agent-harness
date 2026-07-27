# RELEASE_RUNBOOK — agent-harness v1.4.1

**When (UTC):** 2026-07-27  
**Score:** 100 (pr_validator)  
**Infra:** N/A (no vps_infra_ops skill on this product)

## Scope

- `scripts/smoke_unit.sh` + product_plugin unit smoke  
- `vault_fs.py` + `ensure_vault_group_write.py`  
- night_shift / sync_vault_devlog write paths  
- docs/night-shift.md vault ACL section  

## Smoke

| Step | Result |
|------|--------|
| hardcodes | pass |
| unit (`smoke_unit.sh`) | pass |
| validate full | 5/5 |

## §9

1. sudo -n secondbrain tee is optional fallback  
2. One-time vault --apply --sudo is operator  
3. kanban write not fully on vault_fs (follow-up)  

## Rollback

```bash
git checkout v1.4.0
# or: git revert be02817..HEAD
```

## Tag

`v1.4.1`
