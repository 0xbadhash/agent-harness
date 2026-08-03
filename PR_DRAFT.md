# PR Draft — CODER P2–P3 overlay

**Range:** 375e8e149f9c142a960d7ab198aec891fdabe047..HEAD  
**Spec waiver:** docs-only

## What Problem This Solves
LLMs lacked a session Organize pack and explicit mapping from prompt patterns / CODER modes to skills.

## Why This Change Was Made
P2: labels + session_context.py. P3: prompt-patterns.md. No new FSM.

## User Impact
session_context --write; clearer skill modes; pattern catalog.

## Evidence pack
| Item | Result |
|------|--------|
| hard_gates | score |
| unittest | test_session_context |
| smoke | product_smoke |
| validate | full |

## Evidence
```text
TDD N/A for pure docs parts; green_cmd: python3 -m unittest tests.test_session_context
```

## Red-proof
- red_cmd: n/a docs + small script with unit tests first
- green_cmd: python3 -m unittest tests.test_session_context

## Traceability
| AC | Test / evidence |
|----|-----------------|
| CODER labels | ship-flow-detailed + skills-catalog Mode columns |
| session_context | tests/test_session_context.py |
| prompt-patterns | docs/prompt-patterns.md |

## Threat notes
- Asset: process truth
- Abuse: treating Reason as hard gate — catalog forbids

## Things that look bad but are actually fine
1. CODER is teaching overlay not pipeline
2. Pattern names are informal mappings
3. session_context reads harness morning triage for portfolio view
