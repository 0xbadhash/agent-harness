# agent-harness (global)

**Portable AI agentic workflow** — skills, ship pipeline scripts, and policy.  
**Not a product.** Products (watchlist, etc.) plug in via `.agents/product_plugin.yaml`.

## Why

| Layer | Location | Changes when? |
|-------|----------|----------------|
| **Harness** | this repo (`AGENTS_HARNESS_ROOT`) | Process/skills improve |
| **Product** | each product git repo | Features, UI, domain |

Start a new product → install harness → fill product plugin → develop without touching other products.

## Layout

```
agent-harness/
  README.md
  product_plugin.example.yaml
  install_into_product.sh
  policy/          # ENGINEERING_ASSURANCE, AGENT_WORKFLOW, base_constraints, …
  skills/          # portable SKILL.md (execute_dev, pr_review, …)
  scripts/         # pipeline_state, validate, pr_validator, vault sync, …
  templates/       # pipeline.json
  docs/HARNESS.md  # conceptual home
```

**Not included (product-specific):**

- `vps_infra_ops` (hosts, deploy topology)
- Product roadmap, design docs, app source
- Live pipeline state (lives in each product)

## Install into a product

```bash
export AGENTS_HARNESS_ROOT=/home/debian/agent-harness   # or your clone path
cd /path/to/your-product
"$AGENTS_HARNESS_ROOT/install_into_product.sh"
cp "$AGENTS_HARNESS_ROOT/product_plugin.example.yaml" .agents/product_plugin.yaml
# edit product_plugin.yaml for smoke/vault/paths
```

What install does:

1. Ensures `.agents/state/pipeline.json`, `traces/`, `artifacts/`
2. **Rsyncs** portable `skills/` and `scripts/` into the product (overwrites harness files)
3. Copies policy into `.agents/policy/` (reference; product may keep root ENGINEERING_ASSURANCE)
4. Does **not** remove product-only skills (e.g. `vps_infra_ops`)

## Ship sequence (same as before)

```
/execute_dev → /cross_review → /pr_review --validate
→ product infra skill (if any) → /release_mgmt → /sync_docs
```

## Environment

| Var | Purpose |
|-----|---------|
| `AGENTS_HARNESS_ROOT` | Global harness clone |
| `PRODUCT_VAULT_ROOT` / product plugin | Vault root for release notes |
| Product `scripts/` | Prefer product-local copies after install (run from product root) |

## TDD

`/execute_dev` step 3 is mandatory **Red → Green → Refactor** for code changes (see `skills/execute_dev/SKILL.md`).

## Updating harness → all products

1. Change this global repo
2. In each product: re-run `install_into_product.sh` (or pin submodule and pull)
3. Commit vendor refresh in the product repo

## Watchlist

Product lives at `/home/debian/watchlist` with:

- `.agents/product_plugin.yaml` — watchlist smoke/vault/paths
- `.agents/skills/vps_infra_ops/` — **product-only** (not in global)
- Installed portable skills/scripts from this tree
