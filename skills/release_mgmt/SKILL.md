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
7. **Tag** `v$VERSION` (from `VERSION` file) on the release commit.
8. **Phase → shipped** via `scripts/pipeline_state.py set-phase shipped --score <X>`
9. **Origin gate (mandatory — push is not optional):**
   ```bash
   python3 scripts/finish_ship.py --require-push
   # ≡ auto: git push origin HEAD && git push origin --tags
   #   then fetch + fail-closed if origin lacks HEAD or tag v$VERSION
   # SoT: scripts/release_origin_gate.py
   ```
   Halt `🛑 ORIGIN GATE FAIL` if origin is behind HEAD or `git ls-remote --tags origin` lacks `v$VERSION`.
   Do **not** treat push as a later human step. Do **not** claim released until this passes.
10. **Branch cleanup (optional when `gh` available):** delete merged feature branches per product policy.
11. Output: `✅ RELEASED. Run /sync_docs` then honor `NEXT_SKILL=` (qa_campaign only if large)
12. **Post-tag portfolio (default when this repo is agent-harness SoT):** after origin gate PASS:
    ```bash
    python3 scripts/remaining_board.py
    python3 scripts/portfolio_install_report.py --install --force --push
    ```
    Skip portfolio only if `PORTFOLIO_INSTALL=0`.
13. **Unattended deterministic closeout (optional):**
    ```bash
    python3 scripts/run_ship_chain.py --root . --base <task-base> --head HEAD --push
    ```

```
/pr_review --validate → approved → [product infra] → /release_mgmt
  → tag → finish_ship --require-push (auto-push + origin gate) → sync_docs
```
