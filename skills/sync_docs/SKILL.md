---
name: sync_docs
description: Post-release doc drift check, pipeline reset, optional vault release entry.
disable-model-invocation: true
user-invocable: true
max-retries: 0
timeout-seconds: 300
---
# Reads: RELEASE_RUNBOOK.md, product docs, .agents/product_plugin.yaml
# Writes: updated docs as product defines, pipeline → init, optional vault release log
# Anti-patterns: policy/AGENT_REFERENCE.md

When invoked with `/sync_docs`:
1. Pre-condition: phase = shipped (skip vault if user said "don't log" / "ephemeral only")
2. Branch hygiene when `gh` is available (warn on stale non-main branches; do not fail)
3. Run product/doc drift checks if present (`scripts/drift_detector.py` when vendored)
4. Regenerate principle bundles if the product uses them (`scripts/build_principles.py`)
5. Update token audit log if the product uses it
6. **Vault release entry (optional)** — only if `product_plugin.vault` is configured:
   ```bash
   python3 scripts/sync_vault_devlog.py --vault "${PRODUCT_VAULT_ROOT:-$plugin_default}"
   ```
   - Structured **`## date — vX.Y.Z synced`** block
   - Tests / Next priorities from product roadmap when configured
   - Mid-task notes use `--note` (never invent a hand-written `synced` block)
   - Missing vault → `⚠️ VAULT SKIP`; do not fail doc sync
7. Phase → init
8. Output: `✅ DOCS SYNCED.`

Release vault entries are owned by `/sync_docs`, not `/release_mgmt`.
