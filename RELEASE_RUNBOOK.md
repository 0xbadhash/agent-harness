# Release runbook — v1.5.4 (top-50 gap closure)

**Version:** 1.5.4
**Date:** 2026-11-28
**Spec:** `.agents/specs/2026-11-28-top50-gap-closure.md`
**Base:** `origin/main` at `decdd39`
**Head:** `07a4b79` (branch `fix/top50-gaps`)

This is a patch bump. It closes the nine top-50 gaps: the glossary and its gate,
comment routes and the constraint rule, ticket metadata and session write-back,
a detached merge mode, the prototype reference and import check, and the weekly
retro schedule in workflow-harness v0.3.4.

## Smoke

| Step | Command | Exit | Result |
|------|---------|-----:|--------|
| product smoke | `python3 scripts/product_smoke.py --root .` | 0 | 2/2 steps |
| hardcodes | smoke step (`check_hardcodes.py`) | 0 | passed |
| unit | smoke step (`smoke_unit.sh`) | 0 | passed |
| web E2E | `python3 scripts/check_web_e2e.py --root .` | 0 | skipped: no website |
| validate full | `python3 scripts/validate.py full` | 0 | 9/9 gates |
| mypy | `python3 -m mypy scripts tests` | 0 | 245 files |
| pytest | `python3 -m pytest -q` | 0 | 665 passed, 2 skipped, 11 subtests |
| glossary | `python3 scripts/check_glossary.py --root .` | 0 | 29 terms |
| ticket DAG | `python3 scripts/check_ticket_dag.py .../tickets` | 0 | 5 tickets |
| compact safety | `python3 scripts/check_compact_safety.py --root .` | 0 | spec + 5 tickets + glossary |
| workflow-harness | `python3 -m pytest tests -q --ignore=tests/enhancement_specs` | 0 | 229 passed |

## Infra

No infra surface. `product_plugin.yaml` declares no infra skill and
`traits.web` is false. Infra verify skipped.

## Evidence pack

| Item | Result |
|------|--------|
| hard_gates | `hard_gates.py --diff origin/main...HEAD` → pass |
| pr_validator | `pr_validator.py --diff origin/main...HEAD` → 100/100, `approved` |
| pytest | 665 passed, 2 skipped, 11 subtests |
| validate | 9/9 gates |
| smoke | 2/2 steps |

## Rollback

Revert the squash commit. The glossary, checks, and tests are additive; skills
and templates return to their prior text. No data migration.

## Sections that look risky

1. `--constraints` fails many existing comments in a whole-tree run. Opt-in; the
   ship diff is clean.
2. The detached merge returns before completion. The pid and log are the
   contract.
3. The weekly retro commits only when a report exists, with `[skip ci]`.
