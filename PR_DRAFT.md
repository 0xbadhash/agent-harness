# PR Draft: night-shift-log template (Timeline + UTC/HKT)

**Range:** HEAD~1..HEAD (implementation commits)

## What Problem This Solves

Vault night-shift logs mixed formats (no Timeline vs post-rotate Timeline; UTC-only vs dual HKT), so operators could not scan PASS/FAIL history consistently across products.

## Why This Change Was Made

Single SoT helper module renders the operator-requested template on every readiness write and on rotate, so products stay consistent after harness install.

## User Impact

- Every new `01-Projects/<id>/night-shift-log.md` has a Timeline table (newest first) and dual **UTC · HKT** stamps.
- Rotate after PASS still compacts full reports but keeps the same template (no alternate intro schema).

## Evidence

```text
red_cmd: pytest tests/test_night_shift_log_template.py  # missing module / failed asserts
green_cmd: pytest -q  # 22 passed
green_cmd: python3 scripts/validate.py full
green_cmd: python3 scripts/product_smoke.py --root .
```

## Red-proof

- Added `tests/test_night_shift_log_template.py` first (failed: missing `scripts/night_shift_log.py`).
- Implemented module + wired readiness/rotate → 8/8 template tests green; full suite 22 passed.

## Cross-review

_Pending /cross_review_

## Things that look bad but are actually fine

1. `.agents/` remains gitignored for local installs; tracked SoT is `scripts/` + `docs/`.
2. Legacy UTC-only Timeline rows are kept without inventing HKT.
3. night_shift still never release/push/auto-fix product code.
4. Dual Python import path insert for `scripts/` is intentional for product installs.
5. Rotate may leave only the latest full report while Timeline keeps history — intentional spam control.
