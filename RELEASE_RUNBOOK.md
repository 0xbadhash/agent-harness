# Release runbook — v1.5.2 (runner-label gate & post-release evidence)

**Version:** 1.5.2
**Date:** 2026-11-28
**Spec:** `.agents/specs/2026-11-28-runner-label-gate.md`
**Base:** `origin/main` at `7f955f5`
**Head:** `bdfd12b` (squash merge of PR #70)
**Ship PR:** https://github.com/0xbadhash/agent-harness/pull/70
**Legacy PRs (documented, untouched):** `#40`, `#21`, `#19`

This is a patch bump. Adds the `workflow_runners` hard gate, registers it in
`hard_gates.py`, and records two read-only reports: a top-50 re-score against
the shipped trees and a triage of the three open PRs.

## Smoke

| Step | Command | Exit | Result |
|------|---------|-----:|--------|
| product smoke | `python3 scripts/product_smoke.py --root .` | 0 | 2/2 steps |
| hardcodes | smoke step (`check_hardcodes.py`) | 0 | passed |
| unit | smoke step (`smoke_unit.sh`) | 0 | passed |
| web E2E | `python3 scripts/check_web_e2e.py --root .` | 0 | skipped: no website |
| validate full | `python3 scripts/validate.py full` | 0 | 9/9 gates |
| pytest | `python3 -m pytest -q` | 0 | 636 passed, 2 skipped, 11 subtests |
| runner gate | `python3 scripts/check_workflow_runners.py --root .` | 0 | 2 workflows, 1 label declared |

## Infra

No infra surface. `product_plugin.yaml` declares no infra skill and
`traits.web` is false. Infra verify skipped.

## Evidence pack

| Item | Result |
|------|--------|
| hard_gates | `hard_gates.py --diff origin/main...HEAD` → pass |
| pr_validator | `pr_validator.py --diff origin/main...HEAD --strict-cross-review` → 100/100, `approved` |
| pytest | 636 passed, 2 skipped, 11 subtests |
| validate | 9/9 gates |
| smoke | 2/2 steps |
| secrets | clean on `origin/main...HEAD` |
| reports | re-score and triage written under `/srv/boxdrop/out/` |

## Rollback

Revert squash commit `bdfd12b` and re-run `python3 scripts/validate.py full`.
The two reports are outside the repo and additive; remove them if the gate is
reverted.

## Things that look bad but are actually fine

1. Legacy PRs `#40`, `#21`, and `#19` remain open. Their triage is in
   `/srv/boxdrop/out/TRIAGE-PRS-2026-11-28.md`; closing needs operator approval.
2. The new gate skips on repos without `.github/allowed-runners.txt`. That is
   the opt-in: the allowlist is a repo's statement of which runners exist.
3. `check_compact_safety.py --root .` exits 1 because the repo has no
   `GLOSSARY.md`. The re-score records this as item 1; it is not caused by the
   runner gate.
4. The reports carry no tests. They are read-only evidence with a pinned commit
   and an exit code per row.

## Next

`/sync_docs`, then the pipeline returns to `init`.
