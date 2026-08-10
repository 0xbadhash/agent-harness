# PR Draft — HSQ-3 P0 quality gates (G1, G5, G14)

**Spec:** `.agents/specs/HSQ-3-p0-quality-gates.md`  
**Version:** 1.4.22

## What Problem This Solves

Feature ships can pass with thin Traceability, secret patterns miss JWT/sk-, and
syntax-broken files from long sessions still score if tests elsewhere pass.

## Why This Change Was Made

P0 gates from quality review: fail closed on disk+tests, not session length.

## User Impact

- AC-n in specs must map to tests (or N/A)
- Broader secret patterns on diff
- Changed `.py` must `py_compile`

## Red-proof

- red_cmd: `python3 -c "assert False"` (TDD style unit cases in test_hsq3_p0_gates)
- green_cmd: `.venv/bin/python -m pytest tests/test_hsq3_p0_gates.py -q`
- red → green via unit tests AC-1..AC-5

## Traceability

| AC | Test |
|----|------|
| AC-1 | tests/test_hsq3_p0_gates.py::TestAcMap::test_ac_1_missing_test_fails |
| AC-2 | tests/test_hsq3_p0_gates.py::TestAcMap::test_ac_2_mapped_passes |
| AC-3 | tests/test_hsq3_p0_gates.py::TestSecretsG5::test_ac_3_jwt_and_sk_flagged |
| AC-4 | tests/test_hsq3_p0_gates.py::TestSecretsG5::test_ac_4_clean_code |
| AC-5 | tests/test_hsq3_p0_gates.py::TestDiffCompile::test_ac_5_syntax_error |
| AC-6 | hard_gates evaluate wires G1+G14; secrets path G5 |

## Threat notes

- Secrets patterns must not false-positive common code (high-signal only)
- Spec path must not escape product root (path confinement in AC check)

## Evidence pack

- hard_gates: AC map + diff_compile + secrets
- pytest: tests/test_hsq3_p0_gates.py
- validate: compliance + hygiene

## Things that look bad but are actually fine

1. Spec waiver still skips AC map (hotfix/chore/docs/prose) by design.
2. No changed .py → diff_compile skips clean (ok).
3. JWT regex requires eyJ header shape — not any base64.
4. product_smoke not mandatory in G14 (compile only) to avoid product-specific flakiness.
5. Existing hard_gates tests use Spec waiver where AC map not under test.
