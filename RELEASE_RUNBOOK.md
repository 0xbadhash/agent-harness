# Release runbook — v1.5.3 (Codex & Claude Code watcher lanes)

**Version:** 1.5.3
**Date:** 2026-11-28
**Spec:** `.agents/specs/2026-11-27-auto-review-relay.md`
**Base:** `origin/main` at `7f955f5`
**Head:** `main` (`5aed183` + release commit)

This is a patch bump. Un-defers Codex and Claude Code in `deploy/auto-review-relay.py` under the single-writer tmux `--watch` rule (`HOOKED_HARNESSES = {"grok"}`), extends `STRONG_OPTION` for Codex's `›` glyph, and adds fixture-based watcher tests.

## Smoke

| Step | Command | Exit |
|------|---------|------|
| hardcodes | `python3 scripts/product_smoke.py --root .` → `scripts/check_hardcodes.py` | 0 |
| unit | `python3 scripts/product_smoke.py --root .` → `bash scripts/smoke_unit.sh` | 0 |
| product smoke | `python3 scripts/product_smoke.py --root .` | 0 (2/2) |
| web E2E | `python3 scripts/check_web_e2e.py --root .` | 0 (skipped: no website) |
| validate full | `python3 scripts/validate.py full` | 0 (9/9 gates) |
| auto-review tests | `python3 -m pytest -q tests/test_auto_review_*.py` | 0 (36 passed) |

## Infra

No infra surface. `product_plugin.yaml` has no infra skill and `traits.web` is false. Infra verify skipped.

## Evidence pack

| Item | Result |
|------|--------|
| hard_gates | `hard_gates.py --diff origin/main...HEAD` → pass |
| pr_validator | `pr_validator.py --diff origin/main...HEAD` → score 100 (`approved`) |
| smoke | 2/2 steps |
| pytest | 36 passed (`tests/test_auto_review_*.py`) |
| validate | `validate.py full` → 9/9 gates |
| secrets | clean on `origin/main...HEAD` |

## Rollback

Revert commit `5aed183` (`git revert 5aed183`) and re-run `python3 scripts/validate.py full`.

## Things that look bad but are actually fine

1. `codex` CLI is not installed on this host (`codex: command not found`), so its card fixture is derived from recorded prompt layout and verified via `AUTO_REVIEW_TMUX_FIXTURE`.
2. `HOOKED_HARNESSES` remains `{"grok"}` so `--watch` acts as the single writer for both `claude` and `codex`.
3. `check_web_e2e.py` skips because `agent-harness` has no website/browser surface.
