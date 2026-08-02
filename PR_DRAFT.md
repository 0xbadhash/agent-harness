# PR Draft — P0–P1 feedback loops

**Range:** dcb3093125fd03b676ad862b0376c1500f9d5764..HEAD  
**Spec:** `.agents/specs/2026-08-02-p0-p1-feedback-loops.md`

## What Problem This Solves
Operators re-ask finish/push, night FAIL stuck as TODO, products lag harness, no remaining board.

## Why This Change Was Made
Bounded scripts per inventory P0/P1; no invent-and-ship loop.

## User Impact
Four commands close the feedback gaps with artifacts under .agents/artifacts/.

## Evidence pack
| Item | Result |
|------|--------|
| hard_gates | score |
| unittest | finish_ship, promote, portfolio, remaining |
| smoke | product_smoke |
| validate | full |

## Evidence
```text
green_cmd: python3 -m unittest tests.test_finish_ship tests.test_promote_night_fails tests.test_portfolio_install_report tests.test_remaining_board
```

## Red-proof
- red_cmd: tests fail before scripts exist
- green_cmd: 6 tests OK

## Traceability
| AC | Test / smoke |
|----|----------------|
| A1/A3 finish_ship | test_finish_ship |
| A5/A8 promote | test_promote_night_fails |
| A4 portfolio | test_portfolio_install_report |
| A2/B6 remaining | test_remaining_board |

## Threat notes
- Asset: multi-product git push surface
- Abuse: silent portfolio push — requires --install --push

## Things that look bad but are actually fine
1. finish_ship does not spawn LLM skills
2. portfolio lag exit 1 is intentional residual signal
3. promotion stubs optional (--write-stubs)
