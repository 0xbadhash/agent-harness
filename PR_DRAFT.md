# PR Draft — P0 unattended + remediate

**Range:** 85080cd4543454960e61a49352facac9a495e25b..HEAD  
**Spec:** `.agents/specs/2026-08-02-p0-unattended-and-remediate.md`

## What Problem This Solves
Manual FSM re-asks; night FAIL parked; portfolio reinstall forgotten.

## Why This Change Was Made
Deterministic chain + bounded remediate + default portfolio push.

## User Impact
run_ship_chain / night_fail_remediate; harness release reinstalls products.

## Evidence pack
| Item | Result |
|------|--------|
| hard_gates | ok |
| unittest | 3 OK |
| smoke | product_smoke |
| validate | full |

## Evidence
```text
green_cmd: python3 -m unittest tests.test_run_ship_chain tests.test_night_fail_remediate
```

## Red-proof
- red_cmd: pre
- green_cmd: unittest

## Traceability
| AC | Test |
|----|------|
| chain | test_run_ship_chain |
| remediate | test_night_fail_remediate |

## Threat notes
- Asset: multi-product push
- Abuse: no invent features

## Things that look bad but are actually fine
1. Minimal review markers
2. Remediaten leaves domain bugs
3. Portfolio only on harness SoT
