# PR Draft: night_shift dev-deps preflight

## What Problem This Solves
Nightly multi-product readiness FAILs from missing pytest when products lack .venv tooling.

## Why This Change Was Made
Preflight ensure_product_dev_env before each product readiness; create .venv + pip install -r requirements-dev.txt when needed (no sudo pip).

## User Impact
Fewer env FAIL false alarms at 03:15 HKT; real gate failures stay visible.

## Evidence
```
red_cmd: pytest tests/test_ensure_product_dev_env.py  # missing module
green_cmd: pytest -q
green_cmd: python3 scripts/product_smoke.py --root .
```

## Red-proof
Tests failed on missing ensure_product_dev_env.py then passed after implementation.

## Cross-review
CROSS-REVIEW: blockers 0. Security: no sudo pip. Maintainability: pure helper + orchestrator wire. Domain: night_shift hard-stops unchanged.

## Things that look bad but are actually fine
1. Auto-creating .venv is intentional for readiness hosts.
2. Skip when no requirements-dev — readiness may still fail.
3. Dual path load of helper (harness SoT or product scripts/).
4. pip install network-dependent — timeout 600s.
5. Report-only readiness still does not auto-fix product code.
