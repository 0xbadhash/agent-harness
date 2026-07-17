---
name: night_shift
description: Overnight readiness runner (harness SoT) — multi-product suites/security/matrix; vault TODO + logs; 03:15 HKT schedule; human hard-stops. No auto-ship.
disable-model-invocation: true
user-invocable: true
max-retries: 0
timeout-seconds: 3600
preserve-artifacts-on-failure: true
---
# SoT: agent-harness (skills/night_shift + scripts/night_shift_*.py)
# Install into products: install_into_product.sh
# Reads: product_plugin.yaml, .agents/policy/TEST_MATRIX.md (product), config/night_shift_products.yaml
# Writes: per-product vault 01-Projects/<label>/{TODO,night-shift-log}.md + harness-night-shift SUMMARY
# Anti-patterns: docs/AGENT_REFERENCE.md / .agents/policy/AGENT_REFERENCE.md

## Purpose (ORCH-P3 readiness)

Prove each **product test surface** is green so next `/execute_dev` can start.  
**Not** a product UI feature. **Not** autonomous coding overnight.

## Human hard-stops (always)

- **Never** `/release_mgmt`, tag, force-push without explicit user OK.
- **Never** auto-edit product code to “fix” failures (report only).
- **Never** invent roadmap features.
- Failures → vault **TODO** checkboxes only.

## Single product (`/night_shift` in a product checkout)

```bash
python3 scripts/night_shift_readiness.py \
  --vault "${PRODUCT_VAULT_ROOT:-${WATCHLIST_VAULT_ROOT:-/opt/second-brain/vault}}"
```

Flags: `--quick` · `--skip-live` · `--dry-run` · `--root <path>` (when invoking harness SoT copy)

Gates (when scripts exist): test matrix, hygiene, hardcodes, skills, validate full, product_smoke, **coverage** (ORCH-P3b: `check_module_coverage.py --run --soft-if-missing`), optional security, optional live probes from `product_plugin.night_shift`.

**ORCH-TOOLS:** `tools/bin/lint_and_test.sh` → `validate full` (+ optional `--coverage`).

**Vault (per product_plugin.vault.project_label):**

| Path | Content |
|------|---------|
| `01-Projects/<label>/night-shift-log.md` | Append-only full report |
| `01-Projects/<label>/TODO.md` | Recommendations + gate checkboxes |
| `.agents/artifacts/NIGHT_SHIFT_*.md` | Repo mirrors |

## All products (orchestrator — overnight)

```bash
# From agent-harness (SoT) — lives in bin/ (not rsynced into product scripts/)
python3 bin/night_shift_all_products.py \
  --vault "${PRODUCT_VAULT_ROOT:-/opt/second-brain/vault}"
```

Registry: `config/night_shift_products.yaml` (or `$NIGHT_SHIFT_PRODUCTS_FILE`).

**Vault multi summary:**

| Path | Content |
|------|---------|
| `01-Projects/harness-night-shift/SUMMARY.md` | Latest all-product table |
| `01-Projects/harness-night-shift/TODO.md` | Cross-product checkboxes |
| `01-Projects/harness-night-shift/log.md` | Append-only |

## Schedule — **03:15 HKT** (wall clock)

Host runs **UTC**. Timer fires **`19:15 UTC`** = **03:15 next calendar morning in Hong Kong** (HKT = UTC+8).

```bash
# Install once on the VPS (harness units, not per-product):
sudo cp deploy/night-shift-all.service deploy/night-shift-all.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now night-shift-all.timer
systemctl list-timers | grep night-shift-all
# Expect Next: … 19:15:00 UTC
```

Disable legacy watchlist-only timer if present:

```bash
sudo systemctl disable --now night-shift-readiness.timer 2>/dev/null || true
```

## product_plugin optional knobs

```yaml
night_shift:
  default_host: "example.com"   # optional; prefer PRODUCT_BASE_URL env
  live_path: "migration/watchlist.php"
  live_urls: []                 # full URLs to probe for HTTP 200
  live_expect_code: "200"
  coverage_soft: "1"            # "0" = fail hard if coverage tooling missing
```

Coverage config (product or harness): `config/coverage_config.json` (see `config/coverage_config.example.json`).

## Related

- Install: `./install_into_product.sh /path/to/product`
- Hygiene: `/sweep`
- Ship: `/execute_dev` → … → `/sync_docs`
