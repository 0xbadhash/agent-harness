# NIGHT_FAIL_PROMOTIONS

_Generated 2026-08-02 09:36 UTC by promote_night_fails.py_

Repeated night FAIL gates promoted above one-off TODOs.

| Gate | Count | Products | Suggested action |
|------|-------|----------|------------------|
| `validate_full` | 2 | substack-push, watchlist | Add/extend smoke or unit covering gate `validate_full`; or fix root cause in products: substack-push, watchlist |
| `product_smoke` | 2 | substack-push, watchlist | Add/extend smoke or unit covering gate `product_smoke`; or fix root cause in products: substack-push, watchlist |
| `product_fail` | 2 | substack-push, watchlist | Run morning_triage --recheck; open NIGHT_SHIFT_TODO for FAIL products |

## Next

- Fix root causes, then re-run night_shift / morning_triage.
- Optional: `promote_night_fails.py --write-stubs` for placeholder tests.
- This does **not** auto-ship product fixes.

