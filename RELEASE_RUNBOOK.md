# RELEASE_RUNBOOK — agent-harness v1.4.53

**Score:** 100 · phase `approved` → `shipped` · 2026-11-27
**Branch:** `main`
**Tag:** `v1.4.53` (on the release merge commit)
**Scheme:** `VERSION` file, patch bump `1.4.52` → `1.4.53`. Roadmap (`CHANGELOG.md`) lists the hygiene gate.

## Scope

Pristine garden hygiene (T2087U item 2):

- `check_repo_hygiene.check(root, require_clean=False)` fails on backup/scratch
  artifacts and, when asked, on a dirty git tree.
- `hard_gates` runs the hygiene gate for non-prose ships and reports
  `hard_gates: repo_hygiene`.
- `.gitignore` lists the scratch patterns; `config/night_shift_runtime.yaml.bak-t1659u`
  is removed.

## Smoke

| Step | Command | Exit |
|------|---------|------|
| smoke:hardcodes | `python3 scripts/product_smoke.py --root .` → `scripts/check_hardcodes.py` | 0 |
| smoke:unit | `python3 scripts/product_smoke.py --root .` → `bash scripts/smoke_unit.sh` | 0 |
| web_e2e | `python3 scripts/check_web_e2e.py --root .` | 0 (skipped: no website/app UI) |
| validate full | `python3 scripts/validate.py full` | 0 (6/6 gates) |
| pytest | `python3 -m pytest -q` | 0 (479 passed, 2 skipped) |

`product_smoke` summary: `✅ 2 smoke step(s) passed`.

## Infra

No infra surface. `product_plugin.yaml` has no infra skill and `traits.web` is false. Infra verify skipped.

## GitHub PR gate

`gh pr list --state open` returns four pre-existing PRs unrelated to this ship:
#56 `ship/t2088u-fsm-1-5`, #40 `chore/ops-ceo-waits-buzz-leftovers`,
#21 `fix/figure-it-out-night-product-id`, #19
`feat/night-shift-atom-learning-family`. Tagging proceeds with them documented;
this ship does not modify their branches.

## Evidence pack

| Item | Result |
|------|--------|
| hard_gates | pass (pr_validator score 100) |
| pytest | 479 passed, 2 skipped |
| smoke | 2/2 steps, exit 0 |
| validate full | 6/6 gates |
| lint ratchet | E701 held below baseline |
| comment audit | no new history/dead-code/TODO findings on the ship diff |
| correction checks | 5 findings mapped |
| repo hygiene | clean (three pre-existing ticket-less TODO warnings) |

## Rollback

Revert the release commit and the feature commit, then delete tag `v1.4.53`.
`check_repo_hygiene` keeps its CLI behavior; removing the `hard_gates` call
disables the new enforcement. No data or product state is involved.

## Things that look bad but are actually fine

1. `check_repo_hygiene.py` still prints three ticket-less TODO warnings in tests;
   the spec keeps that warning non-failing.
2. `bin/restore_product_venvs.sh` remains untracked and locally excluded; it is a
   restore tool, not scratch state.
3. The clean-tree requirement is off for manual runs and on only inside
   `/pr_review --validate`, so local iteration is unchanged.
4. `validate full` writes `agent-tasks/schema-lint-report.md` to the configured
   vault. This is existing tooling behavior, not a harness-tree edit.
