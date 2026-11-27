# RELEASE_RUNBOOK — agent-harness v1.4.55

**Score:** 100 · phase `approved` → `shipped` · 2026-11-27
**Branch:** `main`
**Tag:** `v1.4.55` (on the release merge commit)
**Scheme:** `VERSION` file, patch bump `1.4.54` → `1.4.55`. Roadmap (`CHANGELOG.md`) lists the categorical lint bans.

## Scope

Categorical lint bans and typed suppressions (T2087U item 4):

- `ruff.toml` selects `B`, `BLE`, `S602`, and `C90` (mccabe 20) with the ratchet
  as the pass/fail signal.
- `compliance_engine.py` calls the ratchet when present.
- `check_type_ignores.py` bans blanket suppressions; every one names `[code]`,
  `owner=…`, and a future `expires=…`.
- 87 unnecessary suppressions removed; eight mypy errors fixed with typed
  annotations; `mypy scripts tests` clean.

## Smoke

| Step | Command | Exit |
|------|---------|------|
| smoke:hardcodes | `python3 scripts/product_smoke.py --root .` → `scripts/check_hardcodes.py` | 0 |
| smoke:unit | `python3 scripts/product_smoke.py --root .` → `bash scripts/smoke_unit.sh` | 0 |
| web_e2e | `python3 scripts/check_web_e2e.py --root .` | 0 (skipped: no website/app UI) |
| validate full | `python3 scripts/validate.py full` | 0 (9/9 gates) |
| pytest | `python3 -m pytest -q` | 0 (507 passed, 2 skipped) |
| mypy | `python3 -m mypy scripts tests` | 0 (Success, 217 files) |

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
| pytest | 507 passed, 2 skipped |
| mypy | Success: no issues in 217 files (zero suppressions) |
| smoke | 2/2 steps, exit 0 |
| validate full | 9/9 gates |
| lint ratchet | B904=1, B905=2, BLE001=44, C901=14 held |
| comment audit | 7 known findings, no increase |
| correction checks | 6 findings mapped |
| type ignores | none in the tree |
| repo hygiene | clean (three pre-existing ticket-less TODO warnings) |

## Rollback

Revert the release commit and the feature commit, then delete tag `v1.4.55`.
Restoring `E,F,W` in `ruff.toml` and deleting the `type_ignores` calls returns the
old gate. The suppression removals are annotation-only; keeping them is harmless.
No data or product state is involved.

## Things that look bad but are actually fine

1. `BLE001=44` and `C901=14` stay in the baseline. The ratchet freezes them and
   the spec names the burn-down follow-up.
2. The diff touches 50 paths. 87 edits are one-line suppression removals; mypy and
   the full suite are green.
3. `compliance_engine` now runs the ratchet instead of raw ruff. Products without
   the script keep the old path.
4. `validate full` writes `agent-tasks/schema-lint-report.md` to the configured
   vault. This is existing tooling behavior, not a harness-tree edit.
