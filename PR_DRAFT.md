# PR Draft — CI matrix steps 1–5

**Spec:** `.agents/specs/2026-08-12-ci-matrix-adoption.md`
**spec_sha256:** 0c816f912a4500a931d0437e1d0891a2283b6644cb2631703a91011f54934411
**Version:** 1.4.26

## What Problem This Solves
No fail-closed product daytime bar; skip-hard-gates too easy; no Semgrep/ZAP/property hooks.

## Why This Change Was Made
CI matrix adoption steps 1–5 + docs/ci-matrix.md.

## User Impact
Daytime CI template, stricter J6 skip, Semgrep, ZAP staging config, property_tests opt-in.

## Red-proof
- red_cmd: `false`
- green_cmd: `true`

## Traceability
| AC | Test |
|----|------|
| AC-1 | tests/test_ci_matrix_steps.py::TestDocsAndTemplates::test_daytime_template_fail_closed |
| AC-2 | tests/test_ci_matrix_steps.py::TestStep2SkipHardGates::test_skip_requires_env |
| AC-3 | tests/test_ci_matrix_steps.py::TestDocsAndTemplates::test_semgrep_config |
| AC-4 | tests/test_ci_matrix_steps.py::TestDocsAndTemplates::test_zap_targets |
| AC-5 | tests/test_ci_matrix_steps.py::TestStep5PropertyTests |
| AC-6 | tests/test_ci_matrix_steps.py::TestDocsAndTemplates::test_ci_matrix_doc |

## Threat notes
- authz: N/A for CI matrix
- secrets: J7 + Semgrep hardcoded pattern
- supply-chain: lockfile audit retained in template

## Evidence pack
- hard_gates + pytest tests/test_ci_matrix_steps.py
- validate / compliance
- docs/ci-matrix.md

## Things that look bad but are actually fine
1. ZAP default warn-only.
2. property_tests disabled by default.
3. install overwrites product daytime-gates.yml (intentional SoT).
4. Semgrep may need network on first CI run.
5. Skip hard gates still exists for emergencies with env+log.
