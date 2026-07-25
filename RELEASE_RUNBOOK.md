# Release runbook — agent-harness v1.3.6

| Field | Value |
|-------|--------|
| **Version** | `v1.3.6` |
| **Date** | 2026-07-25 |
| **Range** | `v1.3.5..v1.3.6` |

## What shipped

| Change | Detail |
|--------|--------|
| `scripts/product_venv.py` | OS-aware venv path; `absolute()` not `resolve()` (Linux symlink keep + Windows Scripts) |
| night_shift + smoke | Wire readiness, all_products, ensure_product_dev_env, product_smoke |
| product_plugin | Multi-entry smoke parse without PyYAML |

## Smoke / tests

| Step | Result |
|------|--------|
| `pytest tests/` | 55+ passed (via product venv pytest) |
| Install into product | `install_into_product.sh` rsyncs scripts/ |

## Rollback

```bash
git checkout v1.3.5
```

## §9

1. absolute() not resolve — required for venv site-packages
2. Dual OS candidate lists — intentional
3. Partial-install fallbacks still list bin/Scripts — safe degrade
