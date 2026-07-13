---
name: release_mgmt
description: Version bump, product smoke (from product_plugin), tag. Optional product infra verify before ship.
disable-model-invocation: true
user-invocable: true
max-retries: 0
timeout-seconds: 600
---
# Reads: PR_DRAFT.md, product roadmap (plugin), .agents/artifacts/INFRA_RUNBOOK.md (if used)
# Writes: RELEASE_RUNBOOK.md, pipeline → shipped
# Anti-patterns: policy/AGENT_REFERENCE.md or product docs/AGENT_REFERENCE.md

When invoked with `/release_mgmt`:
1. **Pre-condition:** `phase = approved` (score ≥95). Else `🛑 WRONG STATE` and halt.
2. **GitHub PR gate (when `gh` is available):**
   - `gh pr list --state open` must be empty, or product policy allows tagging with open PRs documented.
   - Prefer merging release PRs before tagging.
3. **Infra gate (if the product has an infra skill or INFRA_RUNBOOK):**
   - Confirm latest verify PASS within 24h, or run the product's infra skill.
   - If product has no infra surface → skip with note in RELEASE_RUNBOOK.
4. **Bump version** per product semver policy (patch unless roadmap says minor/major).
5. **Run smoke from `.agents/product_plugin.yaml` → `smoke[]`:**
   - For each entry: run `cmd` with optional `cwd` (product root relative).
   - All must exit 0. **Do not** hard-code a language or test runner in this skill.
   - Also run `python3 scripts/validate.py full` when the product vendors harness scripts.
6. **Generate `RELEASE_RUNBOOK.md`** with smoke table, infra reference (if any), rollback, §9 (≥3).
7. **Phase → shipped** via `scripts/pipeline_state.py set-phase shipped --score <X>`
8. **Branch cleanup (optional when `gh` available):** delete merged feature branches per product policy.
9. Output: `✅ RELEASED. Run /sync_docs`

```
/pr_review --validate → approved → [product infra] → /release_mgmt → shipped → /sync_docs
```
