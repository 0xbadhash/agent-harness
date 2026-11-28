# Release runbook — v1.5.1 (auto-review relay & ops closeout)

**Version:** 1.5.1
**Date:** 2026-11-28
**Spec:** `.agents/specs/2026-11-27-auto-review-relay.md`
**Base:** `origin/main` at `f1547d3`
**Head:** `9912f46` (squash merge of PR #68)
**Ship PR:** https://github.com/0xbadhash/agent-harness/pull/68
**Open legacy PRs (unrelated, documented):** `#40`, `#21`, `#19`

This is a patch bump. Adds `deploy/auto-review-relay.py`, systemd unit templates, hook wrapper, Hermes billing-only fallback gate patch, and the ops closeout plan.

## Smoke

| Step | Command | Exit |
|------|---------|------|
| hardcodes | `python3 scripts/product_smoke.py --root .` → `scripts/check_hardcodes.py` | 0 |
| unit | `python3 scripts/product_smoke.py --root .` → `bash scripts/smoke_unit.sh` | 0 |
| product smoke | `python3 scripts/product_smoke.py --root .` | 0 (2/2) |
| web E2E | `python3 scripts/check_web_e2e.py --root .` | 0 (skipped: no website) |
| validate full | `python3 scripts/validate.py full` | 0 (9/9 gates) |
| pytest | `python3 -m pytest tests/ -q` | 0 (619 passed, 3 skipped, 11 subtests) |

## Infra

No infra surface. `product_plugin.yaml` has no infra skill and `traits.web` is false. Infra verify skipped.

## Evidence pack

| Item | Result |
|------|--------|
| hard_gates | `hard_gates.py --diff origin/main...HEAD` → pass |
| pr_validator | `pr_validator.py --diff origin/main...HEAD` → score 100 (`approved`) |
| smoke | 2/2 steps |
| pytest | 619 passed, 3 skipped, 11 subtests |
| validate | `validate.py full` → 9/9 gates |
| secrets | clean on `origin/main...HEAD` |

## Rollback

Revert squash commit `9912f46` (`git revert -m 1 9912f46` or `git revert 9912f46`) and re-run `python3 scripts/validate.py full`.

## Things that look bad but are actually fine

1. Legacy PRs `#40`, `#21`, and `#19` remain open in `0xbadhash/agent-harness` from prior months and are unrelated to `v1.5.1`.
2. `deploy/patches/hermes-fallback-when.patch` lives under `deploy/patches/` because `hermes-agent` is a separate checkout.
3. `check_web_e2e.py` skips because `agent-harness` has no website/browser surface.
