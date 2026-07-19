# Vault dev-log contract (no drift)

**SoT:** agent-harness. Applies to **every** product under `01-Projects/*/dev-log.md` with **no exceptions**.

## Rules

| Rule | Enforcement |
|------|-------------|
| Only writer | `scripts/sync_vault_devlog.py` (release or `--note`) — never freeform `cat >>` / hand MCP dumps |
| Newest first | Writer **prepends**; nightly **normalize** re-sorts |
| UTC + HKT | Every entry has `**When:** … UTC · … HKT` |
| Kinds | `**Kind:** release` or `note` only |
| Night_shift notes | One readiness note per product per UTC day (dedupe) |

## Skills / ship path (systematic)

Any skill that touches vault project history must call the product copy of `sync_vault_devlog.py` (installed from harness):

| Trigger | Writer |
|---------|--------|
| `/sync_docs` | release entry (no `--note`) |
| `/night_shift` / multi-product timer | `--note` readiness (deduped) |
| Mid-task handoff | `--note "title" --bullet …` |
| Freeform edit of `dev-log.md` | **Forbidden** for agents |

## Overnight (no trust in perfect agents)

`night-shift-all.timer` (19:15 UTC / 03:15 HKT) runs `bin/night_shift_all_products.py`, which **always**:

1. Runs readiness for every product in `config/night_shift_products.yaml` (includes ocr-ledger)
2. `normalize_vault_devlog.py --vault $PRODUCT_VAULT_ROOT` on **all** `01-Projects/*/dev-log.md`
3. `check_dev_log_contract.py` — **fails the multi-product job** if any log still drifts

Manual:

```bash
python3 scripts/normalize_vault_devlog.py --vault /opt/second-brain/vault
python3 scripts/check_dev_log_contract.py --vault /opt/second-brain/vault
```

## Product registration

New repo → add to `config/night_shift_products.yaml` + `vault.project_label` / `dev_log_rel` in product_plugin. Missing from the list = not in overnight normalize product gates, but **normalize still scans all** `01-Projects/*/dev-log.md` on disk.
