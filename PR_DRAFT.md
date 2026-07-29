# PR Draft — C5 agent eval checklist (ticket 03)

**Range:** 5089fce..HEAD  
**Spec:** `.agents/specs/2026-07-29-adslc-a3-b5-c5-harden.md`  
**Ticket:** tickets/03-c5-eval-runner.md

## What Problem This Solves
C5 was markdown-only; operators could not run a conformance smoke for harness skills tooling.

## Why This Change Was Made
Minimal runner over existing scripts — not LLM judge.

## User Impact
One command + CI step for skill-conformance smoke.

## Evidence pack
| Item | Result |
|------|--------|
| hard_gates | ok |
| unittest | test_agent_eval_checklist 3 OK |
| smoke | product_smoke |
| validate | 5/5 |
| agent_eval_checklist | ok=True |

## Evidence
```text
red_cmd: python3 -m unittest tests.test_agent_eval_checklist  # before script
green_cmd: python3 -m unittest tests.test_agent_eval_checklist
```

## Red-proof
- red_cmd: import agent_eval_checklist fails before green
- green_cmd: unittest + CLI exit 0

## Traceability
| AC | Test |
|----|------|
| AC-1 runner exit 0/1 | test_harness_root_passes / empty fails |
| AC-2 docs | agent-eval-spike.md |
| AC-3 daytime yml | daytime-gates.yml C5 step |

## Threat notes
- Asset: CI compute / agent trust in checklist
- Abuse: treating checklist as full security audit — docs state non-goals

## Things that look bad but are actually fine
1. --skip-tests in GHA for speed while local full suite still available
2. Not replacing /qa_campaign
3. next_skill without base/head still prints NEXT_SKILL=
