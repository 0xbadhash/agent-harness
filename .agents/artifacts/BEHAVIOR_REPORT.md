# BEHAVIOR-REPORT

**Marker:** BEHAVIOR-REPORT
**Contract:** `hard_gates` fails closed when scratch state, a `.bak` sibling, or an uncommitted path is present
**Surface:** `scripts/check_repo_hygiene.py`, `scripts/hard_gates.py`

## Results

| Clause | Status | Evidence |
|--------|--------|----------|
| 1 Scratch patterns fail | pass | `tests/test_repo_hygiene.py::TestScratchArtifacts::test_each_scratch_pattern_fails` covers `x.bak-1`, `x.orig`, `x.rej`, `.coverage`, `.coverage.abc123`, `.venv-oldbak`, `signal-cli-canary-1`; all report `fail: scratch artifact present`. |
| 2 Dirty tree fails, commit clears it | pass | `test_dirty_repo_fails_when_required` initializes a temp repo, leaves an untracked file, sees the failure, commits it, and observes a pass. |
| 3 Non-repo warns | pass | `test_non_repo_is_a_warning` asserts ok plus a `warn:` message. |
| 4 Gate wiring exercised | pass | `tests/test_hard_gates.py::test_repo_hygiene_blocks_code_ship` asserts `hard_gates: repo_hygiene`; `::test_repo_hygiene_skips_for_prose` asserts the prose skip. |
| 5 Live repo is clean of scratch | pass | `python3 scripts/check_repo_hygiene.py` reports `repo hygiene ok` with only the pre-existing TODO warnings. |

## Summary

- pass: 5 · fail: 0 · blocked: 0 · out_of_scope: 0
- NEXT_SKILL=/pr_review --validate
