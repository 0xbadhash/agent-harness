# RELEASE_RUNBOOK — agent-harness v1.4.54

**Score:** 100 · phase `approved` → `shipped` · 2026-11-27
**Branch:** `main`
**Tag:** `v1.4.54` (on the release merge commit)
**Scheme:** `VERSION` file, patch bump `1.4.53` → `1.4.54`. Roadmap (`CHANGELOG.md`) lists the Markdown escape-hatch audit.

## Scope

Markdown escape hatch (T2087U item 3):

- `check_comment_audit` flags justification prose (`escape_hatch`) unless the line
  names a check; whole-tree runs ratchet against a per-`path::kind` baseline.
- `check_markdown_audit` caps `AGENTS.md` at 250 lines and requires every
  `## Do not` bullet to name an enforcing check.
- `check_stale_agent_config` calls the cap; `validate.py full` runs both audits;
  `hard_gates` reports `markdown_audit`.
- `check_repo_hygiene` fails on `[DEBUG-…]` tags.

## Smoke

| Step | Command | Exit |
|------|---------|------|
| smoke:hardcodes | `python3 scripts/product_smoke.py --root .` → `scripts/check_hardcodes.py` | 0 |
| smoke:unit | `python3 scripts/product_smoke.py --root .` → `bash scripts/smoke_unit.sh` | 0 |
| web_e2e | `python3 scripts/check_web_e2e.py --root .` | 0 (skipped: no website/app UI) |
| validate full | `python3 scripts/validate.py full` | 0 (8/8 gates) |
| pytest | `python3 -m pytest -q` | 0 (497 passed, 2 skipped) |

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
| pytest | 497 passed, 2 skipped |
| smoke | 2/2 steps, exit 0 |
| validate full | 8/8 gates |
| lint ratchet | E701 held below baseline |
| comment audit | 7 known findings, no increase |
| correction checks | 6 findings mapped |
| markdown audit | clean (no `AGENTS.md`; three `## Do not` sections edited) |
| repo hygiene | clean (three pre-existing ticket-less TODO warnings) |

## Rollback

Revert the release commit and the feature commit, then delete tag `v1.4.54`.
Deleting the two `validate.py` gate calls and the `hard_gates` `markdown_audit`
call restores the old behavior. No data or product state is involved.

## Things that look bad but are actually fine

1. Seven legacy comment findings remain in the baseline; the ratchet blocks new
   ones and rewards declines.
2. `check_markdown_audit.py` prints `ok: no AGENTS.md` in this repo. The 250-line
   cap is exercised by tests and applies to product trees.
3. Installed `.agents/skills` copies lag `skills/`; the scanner reads the SoT tree
   only and `install_into_product.sh` refreshes the copies.
4. `validate full` writes `agent-tasks/schema-lint-report.md` to the configured
   vault. This is existing tooling behavior, not a harness-tree edit.
