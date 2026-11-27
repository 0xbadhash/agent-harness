# PR Draft: Correction → check (T2087U item 1)

**Range:** `origin/main..HEAD`

## Summary

- Wire the existing lint ratchet and comment audit into the fail-closed `hard_gates` pack.
- Add `scripts/check_correction_checks.py`: every accepted review finding names a check or a signed `no-check` reason.
- Document the rule and the `## Correction checks` artifact section in `skills/code_review/SKILL.md`.
- Includes one prior commit that lands skill text already expected by main's committed T2086U tests, so main is green before this ship.

## What Problem This Solves

Before this change, `/pr_review --validate` could pass with a lint regression, a new history/dead-code comment, or review findings recorded only as prose. The ratchet ran only in daytime CI, the comment audit ran only in unit tests, and nothing connected an accepted finding to a deterministic check. Corrections therefore stayed in review notes, where the next agent reads them as optional.

## Why This Change Was Made

The source talk's rule at 3:10 is to turn each correction into a deterministic check. Both checks already existed; this change wires them into the local ship gate and adds the missing finding → check map. The alternative (leave the ratchet in CI) was rejected because the local `/pr_review --validate` pack is what blocks a push.

## User Impact

Harness operators and agents see earlier, named failures from `/pr_review --validate`. A product with an older `CODE_REVIEW.md` must add a `## Correction checks` section; the failure message states the heading. No runtime API or product behavior changes.

## Merge Danger

**Door:** two-way
**Blast Radius:** local

## Smallest visual change

The smallest slice is one command: `python3 scripts/check_correction_checks.py --root .` exits 1 when the review map is missing and 0 when every finding is mapped.

## Before/after

Before, the new checks did not exist in the pack:

```text
$ python3 -m pytest tests/test_correction_checks.py -q
E   ModuleNotFoundError: No module named 'check_correction_checks'
```

After, the same tests and the integration test pass:

```text
$ python3 -m pytest tests/test_correction_checks.py tests/test_comment_audit.py \
    tests/test_lint_ratchet.py tests/test_hard_gates.py -q
79 passed
```

## Evidence

```text
targeted: 79 passed (checker + hard_gates tests)
suite: 477 passed, 2 skipped
smoke: bash scripts/smoke_unit.sh
```

## Evidence pack

| Item | Result |
|------|--------|
| hard_gates | run in `/pr_review --validate` |
| pytest | 477 passed, 2 skipped |
| smoke | `bash scripts/smoke_unit.sh` exits 0 with the repaired suite |
| lint ratchet | `python3 scripts/check_lint_ratchet.py` holds at baseline |

## Spec

**Spec:** `.agents/specs/2026-11-27-correction-checks.md`
**Plan:** `.agents/specs/2026-11-27-correction-checks-plan.md`

## Traceability

| AC | Test / smoke |
|----|----------------|
| AC-1 ratchet regression fails | `tests/test_lint_ratchet.py` |
| AC-2 diff comment audit | `tests/test_comment_audit.py` |
| AC-3 correction map | `tests/test_correction_checks.py` |
| AC-4 hard_gates wiring | `tests/test_hard_gates.py::test_new_checks_block_code_ship` |
| AC-5 skill documentation | `python3 scripts/verify_skills.py` + review of `skills/code_review/SKILL.md` |
| AC-6 unit tests | `python3 -m pytest -q` |
| AC-7 smoke | `bash scripts/smoke_unit.sh` |
| AC-8 no secrets | `python3 scripts/check_secrets_diff.py` in hard_gates |

## Threat notes

- Asset / trust boundary: **secrets** in the diff stay covered by `check_secrets_diff.py`; the new checks read repo-local files and run `git diff` and `ruff` with fixed arguments.
- Abuse case / mitigation: a reviewer can write `no-check: <reason>`, but the reason is length-checked and stays visible in the artifact; the map itself cannot be omitted.
- Failure mode / **supply-chain**: a missing `ruff` fails the gate closed with an install/`--report` message; the gate never downloads a tool.

## Red-proof (process honesty)

Red was observed before implementation: `python3 -m pytest tests/test_correction_checks.py -q`
exited with `ModuleNotFoundError: No module named 'check_correction_checks'`.
The retained green command is executable:

```text
green_cmd: python3 -m pytest tests/test_lint_ratchet.py tests/test_correction_checks.py tests/test_comment_audit.py tests/test_hard_gates.py -q
```

## Cross-review

**Marker:** CROSS-REVIEW

Self-check for this small harness slice: the new gate calls use the same
`(ok, messages)` contract as the existing pack; no product code is touched; the
prerequisite commit only lands text that main's committed tests already assert.

## Test plan

- [x] Targeted checker tests (red → green)
- [x] Full `pytest` suite
- [x] `bash scripts/smoke_unit.sh`
- [x] `python3 scripts/check_lint_ratchet.py`

## Things that look bad but are actually fine

1. `CODE_REVIEW.md` now requires a new section. That is the contract change; the gate names the exact heading, and reviews with no findings write `- none`.
2. The comment audit runs on added diff lines only. Pre-existing tree comments stay out of scope so an unrelated ship is not blocked.
3. `check_lint_ratchet.check` fails when `ruff` is absent. Failing closed matches the rest of the pack; the repo ships ruff in `.venv` and on PATH.
4. The first commit lands T2086U skill text. It resolves a red main (tests already committed, text left uncommitted) and adds no new T2087U scope.
