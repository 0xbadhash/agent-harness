# RELEASE_RUNBOOK — agent-harness v1.4.56

**Score:** 100 · phase `approved` → `shipped` · 2026-11-27
**Branch:** `main`
**Tag:** `v1.4.56` (on the release merge commit)
**Scheme:** `VERSION` file, patch bump `1.4.55` → `1.4.56`. Roadmap (`CHANGELOG.md`) lists the automation readiness gate.

## Scope

Automation readiness gate before the outer loop (T2087U item 5):

- `check_automation_ready.py` proves the inner loop from the lint ratchet,
  suppression ban, correction map, behavior report, fresh coverage, and owner.
- `--write` records `AUTOMATION_READINESS.md`; `--require-artifact` validates it.
- `attempt_autofix(require_readiness=True)` refuses with `autofix_blocked` and
  runs no fixer without a current artifact.
- `night_shift_readiness.py` wires the flag from the plugin or
  `AUTOFIX_REQUIRE_READY=1`; the harness plugin opts in.

## Smoke

| Step | Command | Exit |
|------|---------|------|
| smoke:hardcodes | `python3 scripts/product_smoke.py --root .` → `scripts/check_hardcodes.py` | 0 |
| smoke:unit | `python3 scripts/product_smoke.py --root .` → `bash scripts/smoke_unit.sh` | 0 |
| web_e2e | `python3 scripts/check_web_e2e.py --root .` | skipped (no website/app UI) |
| validate full | `python3 scripts/validate.py full` | 0 (9/9 gates) |
| pytest | `python3 -m pytest -q` | 0 (520 passed, 2 skipped) |
| mypy | `python3 -m mypy scripts tests` | 0 (Success, 222 files) |
| readiness | `python3 scripts/check_automation_ready.py --owner 0xbadhash --write` | 0 (all rows ok) |

`product_smoke` summary: `✅ 2 smoke step(s) passed`.

## Infra

No infra surface. `product_plugin.yaml` has no infra skill and `traits.web` is false. Infra verify skipped.

## GitHub PR gate

`gh pr list --state open` is checked before tagging; unrelated open PRs are
documented and left untouched.

## Evidence pack

| Item | Result |
|------|--------|
| hard_gates | pass (pr_validator score gate) |
| pytest | 520 passed, 2 skipped |
| mypy | Success: no issues in 222 files |
| smoke | 2/2 steps, exit 0 |
| validate full | 9/9 gates |
| lint ratchet | B904=1, B905=2, BLE001=44, C901=14 held |
| correction checks | 7 findings mapped |
| type ignores | none in the tree |
| readiness artifact | recorded, marker present, all rows ok |

## Rollback

Revert the release commit and the feature commit, then delete tag `v1.4.56`.
Unset `night_shift.require_automation_ready` (or `AUTOFIX_REQUIRE_READY`) to
restore unconditional autofix; the script and artifact are inert otherwise. No
data or product state is involved.

## Things that look bad but are actually fine

1. The harness opts in while installed products default off. Opt-in proves the
   gate on the reference repo without blocking products that lack coverage.
2. Coverage reads 47.8%. The gate checks freshness and presence;
   `check_module_coverage.py` owns the threshold.
3. `AUTOMATION_READINESS.md` is force-added. It is evidence the nightly job reads,
   not a source file, and it stays out of the default ignore paths.
