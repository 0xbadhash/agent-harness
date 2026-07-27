# PR Draft — smoke_unit wrapper + vault group-write

**Date:** 2026-07-27  
**Version:** 1.4.1 (pending release)

## What Problem This Solves
Night shift failed agent-harness product_smoke on unit (bash -c syntax error) and hit vault Permission denied for night-shift-log writes.

## Why This Change Was Made
- Replace nested bash -c smoke with scripts/smoke_unit.sh
- Shared vault_fs writers + ensure_vault_group_write for group-writable vault logs
- Document operator --apply --sudo path

## User Impact
Night shift unit smoke stable; vault logs writable by debian∈secondbrain after one-time ACL fix.

## Evidence
- pytest 87 passed
- product_smoke 2/2
- validate full 5/5 (COMPLIANCE_PYTHON)
- ensure_vault_group_write --check OK after --apply --sudo
- CODE-REVIEW + CROSS-REVIEW + BEHAVIOR-REPORT artifacts

## Things that look bad but are actually fine
1. sudo -n -u secondbrain tee only works with passwordless sudoers (optional fallback)
2. One-time --apply --sudo is operator, not silent every night after group-write set
3. kanban.md write path not fully migrated to vault_fs in this patch (follow-up)
4. smoke falls back to unittest if pytest missing on interpreter
5. .agents/product_plugin tracked despite general .agents ignore exceptions on this path

## Cross-review
See `.agents/artifacts/CROSS_REVIEW.md` (blockers=0).
