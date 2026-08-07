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
5. **Run smoke (plugin-driven):**
   ```bash
   python3 scripts/product_smoke.py --root .
   python3 scripts/check_web_e2e.py --root .
   ```
   - Loads `.agents/product_plugin.yaml` → `smoke[]` (argv + optional cwd).
   - All steps must exit 0. Empty smoke → warn (do not invent a stack).
   - Also run `python3 scripts/validate.py full` when the product vendors harness scripts.
   - **Website / browser-app products (mandatory):** `python3 scripts/check_web_e2e.py --root .` must pass
     (Playwright + Comet S-id sync + surfaces + smoke e2e). Fail release until fixed.
     Opt out only: `web_e2e.enabled: false`. Docs: `docs/web-e2e-comet.md`.
6. **Generate `RELEASE_RUNBOOK.md`** with:
   - smoke table (commands + exit)
   - infra reference (if any)
   - **Evidence pack (B5):** required at score time in PR_DRAFT (`## Evidence pack` with ≥2 of hard_gates / smoke / pytest / validate / coverage / SBOM). Also paste into RELEASE_RUNBOOK: hard_gates summary, smoke table, coverage/SBOM if any.
   - rollback, §9 (≥3)
7. **Phase → shipped** via `scripts/pipeline_state.py set-phase shipped --score <X>`
8. **Branch cleanup (optional when `gh` available):** delete merged feature branches per product policy.
9. Output: `✅ RELEASED. Run /sync_docs` then honor `NEXT_SKILL=` (qa_campaign only if large)
10. **Post-tag portfolio (default when this repo is agent-harness SoT):** after tag + push of harness:
    ```bash
    python3 scripts/remaining_board.py
    # DEFAULT: reinstall + push lagging products (A4)
    python3 scripts/portfolio_install_report.py --install --push
    python3 scripts/finish_ship.py --require-push
    ```
    Skip portfolio only if operator sets `PORTFOLIO_INSTALL=0` or passes explicit report-only for a dry run.
11. **Unattended deterministic closeout (optional):** if reviews already done and you want scripted score→ship→push:
    ```bash
    python3 scripts/run_ship_chain.py --root . --base <task-base> --head HEAD --push
    ```

```
/pr_review --validate → approved → [product infra] → /release_mgmt → shipped → /sync_docs
```
