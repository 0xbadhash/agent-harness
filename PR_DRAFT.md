# PR Draft — night-shift morning triage

**Range:** 87c56739b8a6d092765c5a750690f9baf152e8de..HEAD  
**Spec:** `.agents/specs/2026-08-02-night-shift-morning-triage.md`

## What Problem This Solves
Night FAIL/TODO required manual hunting every morning.

## Why This Change Was Made
Bounded morning aggregate + optional recheck; no unattended ship yet.

## User Impact
One command/timer answers what failed overnight.

## Evidence pack
| Item | Result |
|------|--------|
| hard_gates | pending score |
| unittest | test_night_shift_morning_triage 4 OK |
| smoke | product_smoke |
| validate | full |

## Evidence
```text
red_cmd: python3 -m unittest tests.test_night_shift_morning_triage
green_cmd: python3 -m unittest tests.test_night_shift_morning_triage
```

## Red-proof
- red_cmd: missing module before implement
- green_cmd: unittest green

## Traceability
| AC | Test |
|----|------|
| AC-1 script | tests + CLI |
| AC-2 exit codes | test_cli_all_pass / fail detect |
| AC-3 recheck | test_recheck_can_clear |
| AC-4 docs/timer | night-shift.md + deploy units |

## Threat notes
- Asset: multi-product readiness truth
- Abuse: treating triage as ship authority — docs say no auto-ship

## Things that look bad but are actually fine
1. Exit 1 with SuccessExitStatus for systemd
2. UNKNOWN only if report unreadable
3. Does not clear vault TODO checkboxes
