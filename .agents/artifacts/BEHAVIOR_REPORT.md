# BEHAVIOR-REPORT

**Marker:** BEHAVIOR-REPORT
**Contract:** the outer loop refuses to act unless a current readiness artifact proves the inner loop
**Surface:** `scripts/check_automation_ready.py`, `scripts/night_shift_autofix.py`, `scripts/night_shift_readiness.py`, `.agents/product_plugin.yaml`

## Results

| Clause | Status | Evidence |
|--------|--------|----------|
| 1 Preconditions named | pass | `check` returns one row per precondition; a failure names the remedy. |
| 2 Artifact recorded | pass | `--owner 0xbadhash --write` wrote `.agents/artifacts/AUTOMATION_READINESS.md` with the marker and seven ok rows. |
| 3 Artifact validated | pass | `--require-artifact` rejects missing, stale, and failed artifacts in `TestReadinessArtifact`. |
| 4 Outer loop refuses | pass | `TestAutofixReadinessGate::test_outer_loop_blocked_without_artifact` asserts one `autofix_blocked` record and no fixer call. |
| 5 Opt-in wiring | pass | Harness plugin sets `require_automation_ready: "1"`; `night_shift_readiness.py` passes the flag. |
| 6 Verification set | pass | full pytest 520 passed; smoke 2/2; validate 9/9; mypy clean in 222 files. |

## Summary

- pass: 6 · fail: 0 · blocked: 0 · out_of_scope: 0
- NEXT_SKILL=/pr_review --validate
