# Release runbook — v1.5.0 (T2088U)

**Version:** 1.5.0
**Date:** 2026-11-27
**Spec:** `.agents/specs/2026-11-27-harness-top50-completion.md`
**Base:** `origin/main` at `bec759c` (the top-50 completion merge)
**Head:** the merge of `release/v1.5.0`
**Ship PR:** https://github.com/0xbadhash/agent-harness/pull/64

This is a minor bump. The top-50 completion adds new scripts, skills, gates,
and templates. Existing commands keep their interfaces, and every new gate has
a test or an explicit skip for products without the matching surface.

## Smoke

| Step | Command | Exit |
|------|---------|------|
| hardcodes | `python3 scripts/product_smoke.py --root .` → `scripts/check_hardcodes.py` | 0 |
| unit | `python3 scripts/product_smoke.py --root .` → `bash scripts/smoke_unit.sh` | 0 |
| product smoke | `python3 scripts/product_smoke.py --root .` | 0 (2/2) |
| web E2E | `python3 scripts/check_web_e2e.py --root .` | 0 (skipped: no website) |
| validate full | `python3 scripts/validate.py full` | 0 (9/9 gates) |
| pytest | `python3 -m pytest -q` | 0 (590 passed, 3 skipped, 11 subtests) |

## Infra

No infra surface. `product_plugin.yaml` has no infra skill and `traits.web` is
false. Infra verify skipped.

## Evidence pack

| Item | Result |
|------|--------|
| hard_gates | `hard_gates.py --diff origin/main...HEAD` on the ship range → pass |
| smoke | 2/2 steps |
| pytest | 590 passed, 3 skipped, 11 subtests |
| validate | `validate.py full` → 9/9 gates |
| coverage | `check_module_coverage` passed |
| secrets | clean on `origin/main...HEAD` |
| lint ratchet | B904 held at 1; no new suppressions |
| type ignores | `check_type_ignores.py` clean |
| correction checks | 8 findings mapped in `CODE_REVIEW.md` |
| repo hygiene | clean tree, no scratch artifacts |
| comment audit | clean on `origin/main...HEAD` |
| ticket DAG | 19 tickets, frontier `01, 07, 10, 12, 16, 17` |
| stack plan | 3 layers, 3 chunks, 2850 LOC |

## GitHub PR gate

`gh pr list --state open` returns three pre-existing PRs unrelated to this ship:

- #40 `chore/ops-ceo-waits-buzz-leftovers`
- #21 `fix/figure-it-out-night-product-id`
- #19 `feat/night-shift-atom-learning-family`

None touch the harness scripts in this ship. They are recorded because the
release policy expects open PRs to be documented.

## CI and companion notes

- Ship PR #64: `skill-conformance` pass, `harness-daytime` pass.
- workflow-harness companion PR #13 merged as `c219fe9`; its release is tracked
  separately as v0.3.0 (green main CI required before tagging).
- `review-tiers.yml` has one `self-hosted` job that stays queued when no runner
  is attached. It is not a required check; the merge path is unaffected.

## Rollback

Revert the squash commit for #64, then tag `v1.5.1` with the revert. A partial
revert leaves skills pointing at scripts that no longer exist, so revert the
whole commit. There is no data migration and no external service to unwind.

## Section 9 — what could still go wrong

1. A repo that enabled `lint_ratchet` for JavaScript may see a new baseline if
   `templates/eslint-ratchet/` is copied without reading it. The template is
   opt-in and documents the baseline file it expects.
2. `merge_stack.py` and `run_tickets.py` invoke `gh` and `git` with argument
   lists, but they still act on a real repository. The default is one PR and
   `--auto-merge` is opt-in.
3. `check_comment_audit.py --strict` can fail a PR that adds a comment above the
   policy ratio. The policy names the ratio, and the failure text says which
   file and count.
