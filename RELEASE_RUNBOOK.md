# RELEASE_RUNBOOK — agent-harness v1.4.52

**Score:** 100 · phase `approved` → `shipped` · 2026-11-27
**Branch:** `main`
**Tag:** `v1.4.52` (on the release commit)
**Scheme:** `VERSION` file, patch bump `1.4.51` → `1.4.52`. Roadmap (`CHANGELOG.md`) lists the feature and the hermetic-test fix.

## Scope

Correction → check wiring (T2087U item 1):

- `hard_gates` runs the lint ratchet, a diff-scoped comment audit, and the correction → check map for non-prose ships.
- `check_correction_checks.py` requires `## Correction checks` with one mapped line per accepted finding.
- `/code_review` documents the rule.
- Routing tests no longer read the operator's local green checkpoint.

## Smoke

| Step | Command | Exit |
|------|---------|------|
| smoke:hardcodes | `python3 scripts/product_smoke.py --root .` → `scripts/check_hardcodes.py` | 0 |
| smoke:unit | `python3 scripts/product_smoke.py --root .` → `bash scripts/smoke_unit.sh` | 0 |
| web_e2e | `python3 scripts/check_web_e2e.py --root .` | 0 (skipped: no website/app UI) |
| validate full | `python3 scripts/validate.py full` | 0 (6/6 gates) |
| pytest | `python3 -m pytest -q` | 0 (477 passed, 2 skipped before the release commit; targeted routing tests 23 passed after isolation) |

`product_smoke` summary: `✅ 2 smoke step(s) passed`.

## Infra

No infra surface. `product_plugin.yaml` has no infra skill and `traits.web` is false. Infra verify skipped.

## GitHub PR gate

`gh pr list --state open` returns three pre-existing PRs unrelated to this ship:
#40 `chore/ops-ceo-waits-buzz-leftovers`, #21 `fix/figure-it-out-night-product-id`,
#19 `feat/night-shift-atom-learning-family`. Tagging proceeds with them documented;
this ship does not modify their branches.

## Evidence pack

| Item | Result |
|------|--------|
| hard_gates | pass (pr_validator score 100) |
| pytest | 477 passed, 2 skipped |
| smoke | 2/2 steps, exit 0 |
| validate full | 6/6 gates |
| lint ratchet | E701/E702/W292 held below baseline |
| comment audit | no new history/dead-code/TODO findings on the ship diff |
| correction checks | 4 findings mapped |

## Rollback

Revert the release commit and the feature commit (`9d43bf7`), then delete tag
`v1.4.52`. The three checkers keep their CLI behavior; only the `hard_gates`
calls disappear. No data or product state is involved.

## Things that look bad but are actually fine

1. `validate full` writes `agent-tasks/schema-lint-report.md` to the configured vault. This is existing tooling behavior, not a harness-tree edit.
2. Open PRs remain at tag time. They are older than this ship and documented above.
3. The price of the new gate is one extra `ruff` run per local review. The ratchet already ran in CI and completes in seconds.
4. The release commit includes a test-isolation change. It makes release smoke deterministic and changes no product behavior.
