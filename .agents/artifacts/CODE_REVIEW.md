# CODE-REVIEW — runner-label gate

**Marker:** CODE-REVIEW
**Command / Scope:** `python3 scripts/review_scope.py --base origin/main --head HEAD --json`
→ 13 files, 729 non-test LOC, `prose_only: false`, `skip_heavy_review: false`
**Base:** `origin/main` `7f955f5422438c6f0a2c3cc4d545598426cc71e2`
**Head:** `b5b396627ebc5f055b54f6d077be585a99ff4d2c`

## Standards

- **Naming.** `Finding`, `Report`, `read_allowlist`, `check`, `_load` state what
  they return. The gate id `workflow_runners` matches the script name.
- **Duplication.** The workflow parser exists once; workflow-harness carries a
  separate three-test contract rather than a copy of the checker.
- **Complexity.** `check()` has one loop over workflows and one over jobs; the
  branch count is below the C901 baseline. No new suppression.
- **Error handling.** `_load` returns `(data, reason)` and catches `ImportError`
  and `yaml.YAMLError` specifically. An earlier draft caught `Exception`; the
  lint ratchet rejected it (`BLE001: 45 > baseline 44`), and the refactor kept
  the baseline at 44.
- **Fowler baseline.** No Mysterious Name, Duplicated Code, Feature Envy, Data
  Clumps, Primitive Obsession, Repeated Switches, Shotgun Surgery, Divergent
  Change, Speculative Generality, Message Chains, Middle Man, or Refused
  Bequest found. The dataclasses are plain carriers by design.
- **Comments.** `check_comment_audit.py --diff origin/main...HEAD --strict`
  → no history, dead-code, or ownerless TODO findings. Ratio 0.03
  (1156 comment / 34846 code lines).

## Spec

| AC | Verdict | Evidence |
|----|---------|----------|
| AC-1 exit 0 / 1 and names file, job, label | met | `tests/test_workflow_runners.py` declared and undeclared cases; live fixture prints `fail: .github/workflows/ci.yml:b uses runner self-hosted (not declared)`, exit 1 |
| AC-2 skip without workflows or allowlist; empty allowlist fails a used label | met | `::test_no_workflows_skips`, `::test_no_allowlist_skips`, `::test_empty_allowlist_fails` |
| AC-3 `hard_gates` runs the gate when both inputs exist and skips with a reason otherwise | met | `scripts/hard_gates.py` registration; diff run reports `skip workflow_runners (2 workflow(s) declared)`; prose-only run reports `(prose-only)` |
| AC-4 workflow-harness jobs on `ubuntu-latest`; its test rejects an undeclared `self-hosted` | met | `review-tiers.yml` lines 14 and 40; `tests/test_workflow_runners.py` (3 tests) |
| AC-5 re-score pins both commits, per-item verdict, delta | met | `/srv/boxdrop/out/SCORECARD-GROKBUILD-HARNESS-TOP50-RESCORE-2026-11-28.md` |
| AC-6 triage records supersession evidence and a recommendation | met | `/srv/boxdrop/out/TRIAGE-PRS-2026-11-28.md` |
| Product smoke passes; no secrets | met | `product_smoke.py` 2/2; `check_secrets_diff.py` clean |

No scope creep: the diff adds the gate, its registration, the workflow fix, the
two reports, and the spec/plan/tickets that route them. It does not close PRs,
open issues, or install skills into products.

## Findings

- **Accepted:** one, during implementation. `_load` caught `Exception`, which
  raised BLE001 above the ratchet baseline. Fixed by returning an error reason
  and catching `ImportError`/`yaml.YAMLError`.
- **Rejected:** none.
- **P0:** 0.
- **Follow-ups (not in this diff):** item 1 in the re-score — add `GLOSSARY.md`
  so the collision and compact-safety checks stop returning `N/A`. This diff
  records the gap; it does not fix it.

## Correction checks

- Broad `except Exception` in `check_workflow_runners._load` → lint ratchet rule
  BLE001 (baseline 44 held) and `tests/test_workflow_runners.py::test_unparsable_workflow_fails`

## Tests / smoke run

- `python3 -m pytest -q` → 636 passed, 2 skipped, 11 subtests (49.70s)
- `python3 scripts/validate.py full` → 9/9 gates
- `python3 scripts/product_smoke.py --root .` → 2/2 steps
- `python3 -m pytest tests -q --ignore=tests/enhancement_specs`
  (workflow-harness) → 226 passed
- `python3 scripts/check_secrets_diff.py --base origin/main --head HEAD` → clean
