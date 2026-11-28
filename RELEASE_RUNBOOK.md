# Release runbook — v1.5.5 (agy CLI backend for /challenge)

**Version:** 1.5.5
**Date:** 2026-11-28
**Spec waiver:** chore
**Base:** `origin/main` at `2a17803`
**Head:** `feat/challenge-agy-backend`

This is a patch bump. Routes `/challenge` (`scripts/challenge.py` + `skills/challenge/SKILL.md`) through local Antigravity CLI (`agy -p`, authed as `jeanclaude.mansart@gmail.com`) by default (`gemini-4-carbon-high` round 1, `gemini-4-hydrogen-high` round 2), keeping GLM/DeepSeek behind `--backend api`.

## Smoke

| Step | Command | Exit |
|------|---------|------|
| hardcodes | `python3 scripts/product_smoke.py --root .` → `scripts/check_hardcodes.py` | 0 |
| unit | `python3 scripts/product_smoke.py --root .` → `bash scripts/smoke_unit.sh` | 0 |
| product smoke | `python3 scripts/product_smoke.py --root .` | 0 (2/2) |
| web EE | `python3 scripts/check_web_e2e.py --root .` | 0 (skipped: no website) |
| validate full | `python3 scripts/validate.py full` | 0 (9/9 gates) |
| challenge + skill tests | `python3 -m pytest -q tests/test_challenge.py tests/test_skill_drift.py` | 0 (16 passed) |

## Infra

No infra surface. `product_plugin.yaml` has no infra skill and `traits.web` is false. Infra verify skipped.

## Evidence pack

| Item | Result |
|------|--------|
| hard_gates | `hard_gates.py --diff origin/main...HEAD` → pass |
| pr_validator | `pr_validator.py --diff origin/main...HEAD` → score 100 (`approved`) |
| smoke | 2/2 steps |
| pytest | 16 passed (`tests/test_challenge.py`, `tests/test_skill_drift.py`) |
| validate | `validate.py full` → 9/9 gates |
| secrets | clean on `origin/main...HEAD` |

## Rollback

Revert the squash-merge commit on `main` (`git revert <sha>`) and re-run `python3 scripts/validate.py full`.

## Things that look bad but are actually fine

1. `call_glm` and `call_deepseek` remain in `scripts/challenge.py` behind `--backend api` as explicit fallback.
2. `skills/challenge/SKILL.md` retains GLM/DeepSeek references in the `--backend api` section (also asserted by `tests/test_skill_drift.py`).
3. `check_web_e2e.py` skips because `agent-harness` has no website/browser surface.
