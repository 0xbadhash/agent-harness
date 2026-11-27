# BEHAVIOR-REPORT

**Marker:** BEHAVIOR-REPORT
**Contract:** categorical lint families are on and ratcheted; every type suppression is coded, owned, and current
**Surface:** `ruff.toml`, `config/lint_ratchet_baseline.json`, `scripts/check_type_ignores.py`, `scripts/compliance_engine.py`, `scripts/hard_gates.py`, `scripts/validate.py`

## Results

| Clause | Status | Evidence |
|--------|--------|----------|
| 1 Families selected | pass | `tests/test_lint_config.py` asserts `B`, `BLE`, `S602`, `C90`, and `max-complexity = 20`. |
| 2 Ratchet floor | pass | `check_lint_ratchet.py --update` wrote `B904=1, B905=2, BLE001=44, C901=14`; the check prints four held lines and exits 0. |
| 3 Suppression ban | pass | `tests/test_type_ignores.py` covers blanket, missing owner, expired, annotated, and skip dirs. |
| 4 Tree has no suppressions | pass | `grep '# type:'` finds none in `scripts/` or `tests/`; `mypy scripts tests` reports success in 217 files. |
| 5 Gate wiring | pass | `tests/test_hard_gates.py::test_type_ignores_blocks_code_ship`; `validate.py full` prints `check_type_ignores`. |
| 6 Compliance agrees | pass | `compliance_engine.py` prints type_checker/linter/test_runner all exit 0; `validate.py full` is 9/9. |

## Summary

- pass: 6 · fail: 0 · blocked: 0 · out_of_scope: 0
- NEXT_SKILL=/pr_review --validate
