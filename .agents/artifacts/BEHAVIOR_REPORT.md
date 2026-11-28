# BEHAVIOR-REPORT — runner-label gate

**Marker:** BEHAVIOR-REPORT
**Target:** `scripts/check_workflow_runners.py` CLI, `hard_gates` diff run, and
workflow-harness tests
**Date:** 2026-11-28
**Contract:** `.agents/artifacts/BEHAVIOR_CONTRACT.md`

| Clause | Check | Result |
|--------|-------|--------|
| B1 | `python3 scripts/check_workflow_runners.py --root .` on agent-harness | `pass` — `ok: 2 workflow(s), 1 runner label(s) declared`, exit 0 |
| B2 | Fixture: `runs-on: self-hosted`, allowlist `ubuntu-latest` | `pass` — `fail: .github/workflows/ci.yml:b uses runner self-hosted (not declared)`, exit 1 |
| B3 | `tests/test_workflow_runners.py::test_no_workflows_skips` | `pass` — skip reason contains `no .github/workflows` |
| B4 | `::test_no_allowlist_skips` | `pass` — skip reason contains `allowed-runners.txt` |
| B5 | `::test_empty_allowlist_fails` | `pass` — one finding for `ubuntu-latest` |
| B6 | Fixture `runs-on: [ubuntu-latest, gpu-box]` | `pass` — JSON finding only `gpu-box`, exit 1 |
| B7 | Fixture `runs-on: ${{ matrix.os }}` | `pass` — `ok: 1 workflow(s), 1 runner label(s) declared, 1 unresolved expression(s)`, exit 0 |
| B8 | `::test_unparsable_workflow_fails` | `pass` — reason `cannot parse workflow` |
| B9 | `python3 scripts/hard_gates.py --diff origin/main...HEAD` | `pass` — `skip workflow_runners (2 workflow(s) declared)`, overall `ok=True` |
| B10 | workflow-harness `tests/test_workflow_runners.py` and both jobs | `pass` — 3 passed; `review-tiers.yml` lines 14 and 40 name `ubuntu-latest` |

## Focused suites

- agent-harness `pytest tests/test_workflow_runners.py -q` → 9 passed
- workflow-harness `pytest tests/test_workflow_runners.py -q` → 3 passed
- workflow-harness full suite → 226 passed

## Observations

- The gate is additive: on agent-harness it reports success, and on a repo with
  no allowlist it skips rather than failing. No product behavior changes.
- An expression does not fail and does not pretend to resolve; the output says
  `unresolved expression(s)`, which is the honest limit.
- The only self-application failure observed is unrelated to this gate:
  `check_compact_safety.py` exits 1 because the repo has no `GLOSSARY.md`. It is
  recorded as re-score item 1 and left unchanged.

NEXT_SKILL=/pr_review --validate
