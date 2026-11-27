# Release runbook — v1.4.52 (T2088U)

**Version:** 1.4.52
**Date:** 2026-11-27
**Spec:** `.agents/specs/2026-11-27-harness-wiring-stack-issues.md`
**Base:** `0336317`
**Head:** `12de719` (review artifacts included)

## Smoke

| Step | Command | Exit |
|------|---------|------|
| hardcodes | `python3 scripts/check_hardcodes.py` | 0 |
| unit | `bash scripts/smoke_unit.sh` | 0 |
| product smoke | `python3 scripts/product_smoke.py --root .` | 0 (2/2) |
| web E2E | `python3 scripts/check_web_e2e.py --root .` | 0 (skipped: no website) |

## Evidence pack

| Item | Result |
|------|--------|
| hard_gates | `hard_gates.py --diff 0336317...HEAD` → pass |
| smoke | 2/2 steps |
| pytest | 436 passed, 1 skipped |
| validate | `validate.py full` → 6/6 |
| coverage | `check_module_coverage` passed |
| secrets | clean on `0336317...HEAD` |

## Infra

No `vps_infra_ops` surface for this product; infra gate skipped.

## Open pull requests at release time

`gh pr list --repo 0xbadhash/agent-harness --state open`:

- #40 `chore: ops dashboard CEO-waits + buzz teardown leftovers`
- #21 `fix(night): figure-it-out product_id for schema strict-warn`
- #19 `Register atom-learning-family on night shift`

None of these touch the harness scripts in this ship. They are recorded here
because the release policy expects open PRs to be documented.

## Merge danger

- **Door:** two-way
- **Blast Radius:** harness

## Rollback

1. `git revert <squash-merge-sha>` on `main` and open a revert PR.
2. Re-tag the prior `v1.4.51` if the release tag already points at the bad commit.
3. No data migration or persistent state is involved; product installs keep the
   previous skill text until the next reinstall.

## Things that look bad but are actually fine

1. **The release tag is not local yet.** Main is protected, so the tag must land
   on the squash-merge commit rather than the feature-branch commit.
2. **Three older PRs are open.** They predate this ship and touch other areas.
3. **`workflow-harness` ships separately.** Its glossary and ticket fields are
   committed on `ship/t2088u-glossary-tickets` with its own 128-test suite.
4. **`STACK_PLAN.md` is generated.** It is evidence, not source; rerun
   `scripts/stack_plan.py --write` when tickets change.
