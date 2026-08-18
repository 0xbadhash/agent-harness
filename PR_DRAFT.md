# PR Draft — pipeline/SESSION current + night-log schedule strip

**Spec waiver:** chore  
**Version target:** 1.4.33  

## What Problem This Solves
Stale pipeline task "next after 1.4.6" / SESSION_CONTEXT 1.4.14; vault night-shift-log pasted full When-tests-run table twice.

## Why This Change Was Made
CEO leftovers 5+6 only.

## User Impact
- Local inventory files current  
- Night logs keep one Schedule SoT pointer; no full table copies  

## Red-proof
- red_cmd: `python3 -c "import sys; sys.exit(1)"`
- green_cmd: `python3 -m unittest tests.test_night_shift_log_schedule_strip -v`

## Traceability
| AC | Evidence |
|----|----------|
| Inventory current | pipeline.json task + SESSION_CONTEXT current VERSION · `session_context.py --write` |
| One schedule source | `strip_schedule_tables` + vault rewrite · `tests.test_night_shift_log_schedule_strip` |

## Threat notes
- authz: N/A
- secrets: none

## Evidence pack
| Item | Result |
|------|--------|
| hard_gates | pr_validator |
| unittest | test_night_shift_log_schedule_strip |
| vault check | When tests run=0; Schedule SoT=1 |
| smoke | product_smoke / validate path |

## Things that look bad but are actually fine
1. pipeline/SESSION are gitignored local ops files — refreshed on disk  
2. Historical report prose may still say "see schedule below" without table  
3. No stamp/Playwright  
