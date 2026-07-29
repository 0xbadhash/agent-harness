# PR Draft — ADSLC A3–A5 + Layer B + Layer C

**Date:** 2026-07-29  
**Version:** 1.4.6  
**Spec:** `.agents/specs/2026-07-29-adslc-a3-a5-layer-b-c.md`  
**Plan:** `.agents/specs/2026-07-29-adslc-a3-a5-layer-b-c-plan.md`

## What Problem This Solves
After hard gates, remaining ADSLC gaps: no daytime CI wire-up, install leave stale skills, pipeline lacks structured identity, no spec gate / AC traceability, weak context/threat/release evidence, no retro flywheel, qa_campaign noise on every sync_docs.

## Why This Change Was Made
Implement tickets 01–05 from the ADSLC spec in one coherent release: B1/B2 first, then A3–A5, B3–B5, C1–C5.

## User Impact
Stricter execute_dev entry (spec_gate), richer PR_DRAFT, install --delete-stale-skills + HARNESS_VERSION, daytime GH workflow, retrospect skill, large-only qa_campaign suggestion.

## Evidence
- pytest 107+  
- validate full 5/5  
- product_smoke 2/2  
- hard_gates + new unit tests  

## Red-proof
- red_cmd: `python3 -m unittest tests.test_hard_gates tests.test_spec_gate` (failed before B1/B2)
- green_cmd: `python3 -m pytest tests/ -q` (107 passed)

## Traceability
| AC | Test / smoke |
|----|----------------|
| B1 spec gate | tests/test_spec_gate.py |
| B2 Traceability | tests/test_hard_gates.py |
| A3 daytime CI | .github/workflows/daytime-gates.yml |
| A4 install delete/stamp | install_into_product.sh + removed_portable_skills.txt |
| A5 pipeline identity | tests/test_fsm_conformance.py |
| B3 context pack | scripts/context_pack.py |
| B4 threat notes | tests/test_hard_gates (runtime path) |
| B5 release evidence | skills/release_mgmt/SKILL.md |
| C1 retrospect | skills/retrospect/SKILL.md |
| C2 FSM tests | tests/test_fsm_conformance.py |
| C3 taxonomy | scripts/night_shift_taxonomy.py |
| C4 qa large-only | tests/test_next_skill + test_fsm_conformance |
| C5 eval spike | docs/agent-eval-spike.md |
| Smoke | product_smoke + validate full |

## Threat notes
- Asset: ship score / phase integrity — mitigated by hard_gates + pipeline flock
- Abuse: skip evidence via --skip-hard-gates — emergency only, documented
- Asset: install wipe product skills — mitigated by removed_portable_skills allowlist only

## Things that look bad but are actually fine
1. Single release for five tickets reduces process overhead  
2. qa_campaign default off for small diffs  
3. C5 is docs spike not full eval platform  
4. Install delete only explicit removed list  
5. Spec gate uses PR_DRAFT or pipeline fields  

## Cross-review
See artifacts after review pass.
