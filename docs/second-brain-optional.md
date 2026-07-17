# Optional knowledge vault (second-brain / Obsidian)

**Default: off.** This public harness does **not** require a vault, Obsidian, or any hardcoded host path.

## When to enable

You already use a personal/team knowledge vault (e.g. second-brain) and want:

- Thin product trees: `01-Projects/<id>/{dev-log.md,docs/}`  
- One place for **agent-harness** docs/skills/policies as SoT mirrors  
- Release rows in `dev-log.md` after `/sync_docs`

## How to enable (product)

1. In the **product** `.agents/product_plugin.yaml`:

```yaml
vault:
  enabled: true
  root_env: PRODUCT_VAULT_ROOT   # read this env var
  default_root: ""               # leave empty; set env on the machine
  project_label: my-product
  dev_log_rel: 01-Projects/my-product/dev-log.md
  # optional allowlist; empty → product default discovery
  mirror_docs: []
```

2. On the machine that has the vault:

```bash
export PRODUCT_VAULT_ROOT=/path/to/your/vault   # e.g. /opt/second-brain/vault
python3 scripts/sync_docs_full.py --vault "$PRODUCT_VAULT_ROOT"
# or skip vault:
python3 scripts/sync_docs_full.py --skip-vault
```

3. **Or** orchestrate from a second-brain checkout (batch multi-repo):

```bash
cd /path/to/second-brain
python3 scripts/sync_projects_vault.py --only agent-harness --only my-product
```

## Night shift vault paths

When `/night_shift` runs with a resolvable vault root, it may write:

| Path | Writer |
|------|--------|
| `01-Projects/<project_label>/night-shift-log.md` | per-product readiness |
| `01-Projects/<project_label>/TODO.md` | auto recommendations |
| `01-Projects/harness-night-shift/{SUMMARY,TODO,log}.md` | multi-product orchestrator |

Details: [night-shift.md](night-shift.md). Still optional: missing vault → report only under `.agents/artifacts/`.

## What stays vault-agnostic

| In harness git (public) | Not default |
|-------------------------|-------------|
| skills/, policy/, docs/ | Hardcoded `/opt/second-brain` |
| install_into_product.sh | Assuming Obsidian/Syncthing |
| product_plugin.example with `enabled: false` | Full catalyxt-style agent dump under every product |

## SoT reminder

Even when vault sync is on, **edit skills/policies in agent-harness**, reinstall into products, then re-sync mirrors. See [[source-of-truth]] / `docs/source-of-truth.md`.
