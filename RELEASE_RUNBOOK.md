# Release runbook — v1.4.56 (T2088U)

**Version:** 1.4.56
**Date:** 2026-11-27
**Spec:** `.agents/specs/2026-11-27-harness-wiring-stack-issues.md`
**Base:** `origin/main` at `1e3718d` (v1.4.55)
**Head:** the merge of `origin/main` into `ship/t2088u-fsm-1-5`
**Ship PR:** https://github.com/0xbadhash/agent-harness/pull/56

The version moved to 1.4.56 because main shipped `v1.4.52` through `v1.4.55`
(correction → check, pristine garden, Markdown escape hatch, categorical lint)
while this branch was in review. Every one of those releases is merged into this
branch and re-verified here.

## Smoke

| Step | Command | Exit |
|------|---------|------|
| hardcodes | `python3 scripts/product_smoke.py --root .` → `scripts/check_hardcodes.py` | 0 |
| unit | `python3 scripts/product_smoke.py --root .` → `bash scripts/smoke_unit.sh` | 0 |
| product smoke | `python3 scripts/product_smoke.py --root .` | 0 (2/2) |
| web E2E | `python3 scripts/check_web_e2e.py --root .` | 0 (skipped: no website) |
| validate full | `python3 scripts/validate.py full` | 0 (6/6 gates) |
| pytest | `python3 -m pytest -q` | 0 (520 passed, 1 skipped) |

## Infra

No infra surface. `product_plugin.yaml` has no infra skill and `traits.web` is
false. Infra verify skipped.

## Evidence pack

| Item | Result |
|------|--------|
| hard_gates | `hard_gates.py --diff origin/main...HEAD` → pass |
| smoke | 2/2 steps |
| pytest | 520 passed, 1 skipped |
| validate | `validate.py full` → 6/6 |
| coverage | `check_module_coverage` passed |
| secrets | clean on `origin/main...HEAD` |
| lint ratchet | B904/B905/BLE001/C901 held at baseline |
| type ignores | `check_type_ignores.py` clean |
| correction checks | 4 findings mapped in `CODE_REVIEW.md` |
| repo hygiene | clean tree, no scratch artifacts |
| comment audit | clean on `origin/main...HEAD` |

## GitHub PR gate

`gh pr list --state open` returns three pre-existing PRs unrelated to this ship,
plus this ship's PR:

- #56 `ship/t2088u-fsm-1-5` — this ship (open until squash merge)
- #40 `chore/ops-ceo-waits-buzz-leftovers`
- #21 `fix/figure-it-out-night-product-id`
- #19 `feat/night-shift-atom-learning-family`

None of #40, #21, #19 touch the harness scripts in this ship. They are recorded
because the release policy expects open PRs to be documented.

## CI fix carried by this ship

The new pristine-garden gate failed `harness-daytime` because the J1 coverage
step wrote `.coverage` into the repo root, which `check_repo_hygiene` treats as a
scratch artifact. The workflow now sets `COVERAGE_FILE=.agents/artifacts/.coverage`
and creates that gitignored directory first. Both checks pass on the PR.

## Tag

`v1.4.56` lands on the squash-merge commit on `main`, not on this branch. Main is
protected, so the tag cannot be created from here before the merge.

## Merge danger

- **Door:** two-way
- **Blast Radius:** harness

## Rollback

1. `git revert <squash-merge-sha>` on `main` and open a revert PR.
2. Delete tag `v1.4.56` if it already points at the bad commit.
3. No data migration or persistent state is involved; product installs keep the
   previous skill text until the next reinstall.

## Things that look bad but are actually fine

1. **The release tag is not local yet.** Main is protected, so the tag must land
   on the squash-merge commit rather than the feature-branch commit.
2. **Three older PRs are open.** They predate this ship and touch other areas.
3. **`workflow-harness` ships separately.** Its glossary and ticket fields are on
   `ship/t2088u-glossary-tickets-pr` with its own 128-test suite
   (https://github.com/0xbadhash/workflow-harness/pull/5).
4. **The branch carries commit `0336317`, which is not on main.** It is the base
   repair that main's committed tests already expected (diagnosing-bugs skill,
   review axes, Merge Danger template block, `GLOSSARY.md` references).
5. **Two `type: ignore` comments became casts.** Main's new suppression gate
   requires an owner and expiry on every ignore; the ticket DAG parser did not
   need the ignores once `cast(list[str], …)` made the types explicit.
6. **`STACK_PLAN.md` is generated.** It is evidence, not source; rerun
   `scripts/stack_plan.py --write` when tickets change.
