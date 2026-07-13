---
name: release_mgmt
description: Version bump, production smoke tests, packaging. Requires passing /vps_infra_ops --verify before ship.
disable-model-invocation: true
user-invocable: true
max-retries: 0
timeout-seconds: 600
---
# Pipeline / phase gates: docs/AGENT_REFERENCE.md
# Reads: PR_DRAFT.md, BACKEND_ROADMAP.md, .agents/artifacts/INFRA_RUNBOOK.md
# Writes: RELEASE_RUNBOOK.md, pipeline → shipped
When invoked with `/release_mgmt`:
1. **Pre-condition:** `phase = approved` (score ≥95). Else `🛑 WRONG STATE` and halt.
2. **GitHub PR gate (mandatory when `gh` is available):**
   - `gh pr list --state open --json number,title,headRefName` must return **[]**.
   - If any open PRs → `🛑 OPEN PRS` and halt. Merge (or close) all release PRs on GitHub **before** tagging.
   - **Never** fast-forward `main` from a local feature/stack branch while matching PRs are still open — that bypasses review history and leaves orphan branches.
   - For execute-plan stacks: merge bottom-up (or rollup PR to `main`), confirm all stack PRs show `MERGED`, then proceed.
3. **Infra gate (mandatory):** Run `/vps_infra_ops --verify` in this session, or confirm `.agents/artifacts/INFRA_RUNBOOK.md` exists with all critical checks **PASS** and timestamp within 24h. On fail → `🛑 INFRA BLOCKED` and halt (do not set `shipped`).
4. **Bump version** per semver (patch unless BACKEND_ROADMAP declares minor/major).
5. **Run smoke tests** (all must pass — suite size grows over time; require **green**, not fixed historic counts):
   - `cd migration && php bin/health.php` → exit 0
   - `cd migration && vendor/bin/phpunit` → exit 0 (currently ~262 tests; 0 failures)
   - `PYTHONPATH=. .venv/bin/python -m pytest -q` → exit 0 (currently ~92 tests)
   - `python3 scripts/validate.py full` → 4/4
   - `cd migration && node tests/watchlist-chart.test.js` → stdout `ok`
6. **Generate `RELEASE_RUNBOOK.md`** with smoke table, infra verify reference, rollback, §9 (≥3 entries). Record merged PR numbers and final `main` SHA.
7. **Phase → shipped** via `scripts/pipeline_state.py set-phase shipped --score <X>`
8. **Branch cleanup (mandatory when `gh` is available):** Delete merged stack/feature branches so GitHub does not show stale "Compare & pull request" rows:
   ```bash
   git fetch origin --prune
   gh api repos/{owner}/{repo}/branches --paginate --jq '.[].name' \
     | grep -v '^main$' \
     | while read -r b; do git push origin --delete "$b"; done
   ```
   Skip branches still tied to an **open** PR (should not happen if step 2 passed). Log deleted branch names in the release output.
9. Output: `✅ RELEASED. Run /sync_docs`

**Pipeline sequence (enforced):**
```
/pr_review --validate → approved → merge GitHub PRs → /vps_infra_ops --verify → /release_mgmt → shipped → /sync_docs
```

**Execute-plan stacks:** `/execute-plan` creates branches and (optionally) draft PRs but does **not** merge. After stack PRs are merged on GitHub, run `/release_mgmt` (which enforces step 2 + step 8). `/pr-babysit` monitors CI/comments but also does not merge or delete branches.