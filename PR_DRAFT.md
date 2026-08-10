# PR Draft — HSQ-3 P3 G15 protect SoT pin

**Spec:** `.agents/specs/HSQ-3-p3-protect-sot-pin.md`
**spec_sha256:** 4a75fc6b1ab5ddf97d484eb2503900868696202db91f92b8826b4e9febe6915f
**Version:** 1.4.25

## What Problem This Solves
Products keep forked FSM scripts after protect-list installs; silent drift from HSQ-2 floors.

## Why This Change Was Made
P3 warn-only SoT pin — no install overwrite.

## User Impact
- portfolio report notes SoT pin drift
- CLI check_protect_sot_pin --strict optional

## Red-proof
- red_cmd: `false`
- green_cmd: `true`

## Traceability
| AC | Test |
|----|------|
| AC-1 | tests/test_hsq3_p3_protect_pin.py::TestProtectPin::test_ac_1_identical |
| AC-2 | tests/test_hsq3_p3_protect_pin.py::TestProtectPin::test_ac_2_drift |
| AC-3 | tests/test_hsq3_p3_protect_pin.py::TestProtectPin::test_ac_3_strict_cli |
| AC-4 | portfolio_install_report evaluate notes (manual) |

## Threat notes
- authz: N/A for pin checker
- secrets: N/A

## Evidence pack
- pytest tests/test_hsq3_p3_protect_pin.py
- hard_gates suite
- validate compliance

## Things that look bad but are actually fine
1. Warn-only default — intentional anti-break for product forks.
2. Only pipeline_state + hard_gates pinned (not all protect list).
3. --strict is opt-in for CI products that want fail-closed.
4. mypy fix for P2 security_paths is drive-by.
5. No auto-merge of forks.
