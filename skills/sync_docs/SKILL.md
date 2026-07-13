---
name: sync_docs
description: Post-release drift detection, pipeline reset, and Obsidian vault dev-log sync.
disable-model-invocation: true
user-invocable: true
max-retries: 0
timeout-seconds: 300
---
# Reads: git diff, RELEASE_RUNBOOK.md, WORKFLOW_DOCUMENTATION.md, all docs
# Writes: updated docs, pipeline → init, vault 01-Projects/watchlist/dev-log.md
# Vault root: ${WATCHLIST_VAULT_ROOT:-/opt/second-brain/vault} (see AGENTS.md)
# Anti-patterns: docs/AGENT_REFERENCE.md

When invoked with `/sync_docs`:
1. Pre-condition: phase = shipped (skip vault step if user said "don't log" or "ephemeral only")
2. **Branch hygiene check (when `gh` is available):** `gh api repos/{owner}/{repo}/branches --paginate --jq '.[].name'` should be only `main`. If extra branches remain → `⚠️ STALE BRANCHES: <list>. Run branch cleanup from /release_mgmt step 8 or delete manually.` Do not fail doc sync.
3. Run drift detector on all docs
4. Regenerate ALL_PRINCIPLES.md bundle
5. Update token_audit.log
6. **Vault dev-log — release kind only** (Option A; not ad-hoc `--note`):
   ```bash
   python3 scripts/sync_vault_devlog.py --vault "${WATCHLIST_VAULT_ROOT:-/opt/second-brain/vault}"
   ```
   - Appends structured **`## date — vX.Y.Z synced`** block (Release/Scope/Tests/Next/Pipeline/Repo/Task)
   - Entry includes **Tests** (PHPUnit/pytest/validate + total) and **Next (Shaping)** from `BACKEND_ROADMAP.md` `## Shaping`
   - Idempotent: skips if `{version} synced` already present
   - Mid-task notes use `--note` (see `AGENTS.md`); never mix freeform into release shape
   - On missing vault or permission failure → `⚠️ VAULT SKIP` (stderr); do **not** fail doc sync
7. Phase → init
8. Output: `✅ DOCS SYNCED. Vault: <path>. Ready for next cycle.`

**Release vault entry** is owned by `/sync_docs`, not `/release_mgmt` (see `AGENTS.md`).