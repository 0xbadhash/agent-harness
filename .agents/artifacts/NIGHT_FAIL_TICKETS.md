# NIGHT_FAIL_TICKETS

_Generated 2026-08-02 11:01 UTC by night_fail_remediate.py_

Open after bounded autofix. Close when product readiness is green.

## watchlist (FAIL → FAIL)

- attempt: ensure_dev_env:would run /home/debian/watchlist/scripts/ensure_product_dev_env.py
- attempt: ruff_fix:/home/debian/watchlist/.venv/bin/python -m ruff check --fix scripts tests
- attempt: black_format:/home/debian/watchlist/.venv/bin/python -m black scripts tests
- [ ] [watchlist] fix gate `unknown_gate` until daytime_readiness / product_smoke green

## substack-push (FAIL → FAIL)

- attempt: ensure_dev_env:would run /home/debian/substack-push/scripts/ensure_product_dev_env.py
- attempt: ruff_fix:/home/debian/substack-push/.venv/bin/python -m ruff check --fix scripts tests src
- attempt: black_format:/home/debian/substack-push/.venv/bin/python -m black scripts tests
- [ ] [substack-push] fix gate `unknown_gate` until daytime_readiness / product_smoke green

