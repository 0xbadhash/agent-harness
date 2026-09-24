---
name: sync_docs
description: >
  Post-release doc sync — repo stamps required; knowledge-vault mirror optional
  and off by default (vault-agnostic harness).
disable-model-invocation: true
user-invocable: true
max-retries: 0
timeout-seconds: 600
---

# Anti-patterns: policy/AGENT_REFERENCE.md · base_constraints
# /sync_docs (portable harness)

## Source of truth

- **Skills & shared policies:** `agent-harness` git (reinstall into products).  
- **Product docs & code:** this product repo.  
- **Vault (if any):** mirrors/logs only — see `docs/source-of-truth.md` and `docs/second-brain-optional.md`.

## When invoked

1. **Pre-condition:** Prefer `phase = shipped` (or user mid-cycle force).  
2. Branch hygiene / drift / principles **when those scripts exist**.  
3. **Repo side (always):**
   ```bash
   python3 scripts/sync_docs_full.py --skip-vault
   # or full script; vault skipped unless enabled
   python3 scripts/sync_docs_full.py
   ```
   - Stamp README / PRODUCT markers when present  
   - Update WORKFLOW_DOCUMENTATION Last Release when present  
   - **Product post-hook (optional, harness ≥1.4.47):** if the optional product hook
     `scripts/sync_docs_product.py` exists, `sync_docs_full.py` runs it as
     `<product .venv python> <hook> --post-hook` with `SYNC_DOCS_POST_HOOK=1` after a successful
     sync (not on `--dry-run` / `--skip-repo` / `--help`). Hook exit ≠ 0 → sync_docs exits with
     that code. The hook must never call sync_docs_full again; `SYNC_DOCS_POST_HOOK=1` already
     set → hook skipped (recursion guard). Contract: `run_post_hook` docstring in
     sync_docs_full. No hook file → behavior unchanged.
4. **Vault side (optional — only if enabled):**
   - `product_plugin.yaml` → `vault.enabled: true` **and**  
   - env `$PRODUCT_VAULT_ROOT` (or name in `vault.root_env`) points at a real directory  
   - Then: thin mirror → `01-Projects/<label>/docs/` + `wiki/<label>.md` + release dev-log  
   - **Never** assume `/opt/second-brain` or Obsidian by default  
   - Missing vault → `⚠️ VAULT SKIP` and still finish repo stamps  
5. Phase → `init` via `pipeline_state.py` when product uses the FSM.  
6. Output: `✅ DOCS SYNCED.` + repo files + vault paths or VAULT SKIP.

## Flags

- `--dry-run` / `--skip-vault` / `--skip-repo` / `--force-devlog`  
- `--vault /path` — operator override (still does not hardcode a public default)

## Do not

- Hardcode vault host paths into public harness defaults  
- Mirror full `.agents/skills` trees under every product vault (SoT is harness)  
- Edit vault mirrors as source of truth  
