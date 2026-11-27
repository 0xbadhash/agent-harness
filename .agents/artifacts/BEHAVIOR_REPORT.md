# BEHAVIOR-REPORT

**Marker:** BEHAVIOR-REPORT
**Contract:** `hard_gates` fails closed on a lint regression, a new history comment, and a review without a correction → check map
**Surface:** `scripts/hard_gates.py`, `scripts/check_lint_ratchet.py`, `scripts/check_comment_audit.py`, `scripts/check_correction_checks.py`

## Results

| Clause | Status | Evidence |
|--------|--------|----------|
| 1 Missing correction map fails | pass | On the pre-change `CODE_REVIEW.md` (no `## Correction checks`), `python3 scripts/check_correction_checks.py --root .` printed the missing-section message and exited 1. With the section added it exits 0. |
| 2 Ratchet holds at baseline | pass | `python3 scripts/check_lint_ratchet.py` printed `ratchet: E701 improved 3 → 0` and two more held/improved lines; exit 0. |
| 3 Diff comment audit clean | pass | `python3 scripts/check_comment_audit.py --diff 0336317...HEAD --strict` reports no new history/dead-code/TODO comments on the added lines. |
| 4 Gate wiring exercised | pass | `tests/test_hard_gates.py::test_new_checks_block_code_ship` asserts all three `hard_gates:` violations; `test_new_checks_skip_for_prose` asserts the prose skip list. |

## Summary

- pass: 4 · fail: 0 · blocked: 0 · out_of_scope: 0
- NEXT_SKILL=/pr_review --validate
