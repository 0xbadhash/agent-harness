# RELEASE RUNBOOK — agent-harness v1.3.0

**Date:** 2026-07-18  
**Score:** 100 (pr_validator)  
**Tag:** `v1.3.0`

## Scope

- Canonical vault `night-shift-log.md` template: Timeline (newest-first) + dual UTC/HKT + full reports
- Shared SoT: `scripts/night_shift_log.py`
- Wired into `night_shift_readiness.py` (prepend) and `rotate_night_shift_logs.py` (compact)
- Docs: `docs/night-shift.md` + `docs/specs-2026-07-18-night-shift-log-template.md`
- Tests: `tests/test_night_shift_log_template.py`

## Smoke

| Step | Result |
|------|--------|
| hardcodes | ✅ |
| unit (pytest) | ✅ 22 passed |
| validate full | ✅ 4/4 |

## Infra

N/A (portable harness; no product INFRA_RUNBOOK).

## Open PRs

empty / none required for private harness tag.

## Rollback

```bash
git checkout v1.2.0
# reinstall products from that tag if needed
```

## Things that look bad but are actually fine

1. night_shift never auto-releases products — this release is harness only.  
2. Legacy UTC-only log rows remain until rewritten by new runs.  
3. `.agents/` local installs stay gitignored.  
4. Rotate keeps Timeline + one full report after PASS.

## Next

`/sync_docs` then reinstall scripts into products:
`./install_into_product.sh /path/to/product`
