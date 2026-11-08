# RELEASE_RUNBOOK — agent-harness v1.4.50

**Score:** 100 · phase `approved` → `shipped` · 2026-11-08
**Branch:** `docs/ops-dashboard-contract`
**Tag:** `v1.4.50` (annotated, on the release commit)
**Scheme:** `VERSION` file, patch bump `1.4.49` → `1.4.50`. Roadmap (`CHANGELOG.md`) lists fixes only. Tag name is `v$VERSION`.

## Smoke

| Step | Command | Exit |
|------|---------|------|
| smoke:hardcodes | `python3 scripts/product_smoke.py --root .` → `scripts/check_hardcodes.py` | 0 |
| smoke:unit | `python3 scripts/product_smoke.py --root .` → `bash scripts/smoke_unit.sh` | 0 |
| web_e2e | `python3 scripts/check_web_e2e.py --root .` | 0 (skipped: no website/app UI) |
| validate full | `python3 scripts/validate.py full` | 0 (6/6 gates) |

`product_smoke` summary: `✅ 2 smoke step(s) passed`.

## Infra

No infra surface. No `.agents/artifacts/INFRA_RUNBOOK.md`. `product_plugin.yaml` has no infra skill. `night_shift.live_path` is empty. `traits.web` is false. Infra verify skipped.

## GitHub PR gate

`gh pr list --state open` is not empty:

| PR | Head | Base |
|----|------|------|
| #40 | `chore/ops-ceo-waits-buzz-leftovers` | `main` |
| #21 | `fix/figure-it-out-night-product-id` | `main` |
| #19 | `feat/night-shift-atom-learning-family` | `main` |

None of these is this release branch. `docs/repo-access.md` says public open PRs are fine and only the owner merges to `main`. Agents must not push `main`. These three PRs were already open when `v1.4.42` through `v1.4.49` were tagged. Merging them is a human action. This ship does not merge them.

## Evidence pack

| Item | Result |
|------|--------|
| pipeline | `phase=approved`, `score=100` before tag (`scripts/pipeline_state.py get`) |
| smoke | hardcodes exit 0; unit (`pytest -q` via `scripts/smoke_unit.sh`) exit 0 |
| validate | `python3 scripts/validate.py full` — compliance_engine, check_hardcodes, check_repo_hygiene, check_module_coverage, check_dev_log_contract, vault_schema_lint — 6/6 passed |
| web_e2e | skipped, exit 0 (not a website/app) |
| pytest (score-time, ops-dashboard contract on this branch) | `tests/test_ops_dashboard_contract.py` 4 passed (`PR_DRAFT.md`) |

No coverage percentage and no SBOM were produced by this release path. `check_module_coverage.py` reported the coverage config valid (default 10%).

## Rollback

Previous tag: `v1.4.49`.

```bash
git checkout v1.4.49
```

Do not force-push and do not delete `v1.4.50` from origin from this ship. Withdrawing the tag is a human decision.

## Not in this ship

- No push to `main`. Landing this branch on `main` needs a human merge (branch protection, `docs/repo-access.md`).
- No portfolio `--install --push`. That command commits and pushes other product checkouts' `HEAD`, which may be `main`. Operator authorized this branch and `v1.4.50` only.
- README `Current release` line is still `v1.4.49` until `/sync_docs`. The `v1.4.49` tag itself still said `v1.4.29` in that line.
- Stashed local WIP (ops dashboard script, optional_skills, gitignore, untracked challenge skill and canary) is not in the release commit.

## §9

```yaml
things_that_look_bad_but_are_fine:
  - file: "RELEASE_RUNBOOK.md"
    concern: "Three GitHub PRs are still open at tag time"
    why_fine: "They are not this release. repo-access.md leaves main merges to the owner. The same PRs were open for tags v1.4.42 through v1.4.49."
    validation: "gh pr list --state open --json number,headRefName,baseRefName"
  - file: "README.md:4"
    concern: "Current release line still says v1.4.49 inside the v1.4.50 commit"
    why_fine: "VERSION is the version SoT. README stamp is /sync_docs, which runs after the tag. The v1.4.49 tag's README still said v1.4.29."
    validation: "git show v1.4.49:README.md | head -6; cat VERSION"
  - file: "CHANGELOG.md"
    concern: "v1.4.50 notes only the Unreleased fixes, while HEAD is many commits after v1.4.49"
    why_fine: "The patch bump promotes the roadmap section the repo already wrote. The tag points at HEAD of docs/ops-dashboard-contract, so those commits are in the tagged tree."
    validation: "git log --oneline v1.4.49..HEAD"
  - file: "scripts/ops_dashboard.py"
    concern: "Working tree had unrelated ops-dashboard edits during the ship request"
    why_fine: "The security-root-ioc spec leaves that diff out of scope. Those edits were stashed and are not in the release commit."
    validation: "git show --stat HEAD -- VERSION CHANGELOG.md RELEASE_RUNBOOK.md"
```
