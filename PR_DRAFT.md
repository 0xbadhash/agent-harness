# PR Draft — B5 Evidence pack hard gate (ticket 02)

**Range:** c1ea122..HEAD  
**Spec:** `.agents/specs/2026-07-29-adslc-a3-b5-c5-harden.md`  
**Ticket:** tickets/02-b5-evidence-score.md

## What Problem This Solves
B5 was skill prose only; reviewers could score 100 without a structured evidence pack.

## Why This Change Was Made
Mirror B2/B4 hard_gates pattern for ## Evidence pack with ≥2 tokens.

## User Impact
Agents/operators must fill Evidence pack in PR_DRAFT on code ships before approve.

## Evidence pack
| Item | Result |
|------|--------|
| hard_gates | ok (self) |
| unittest | test_hard_gates 9 OK |
| smoke | product_smoke 2/2 |
| validate | 5/5 |

## Evidence
```text
red_cmd: python3 -m unittest tests.test_hard_gates.TestHardGates.test_evidence_pack_required_for_code
green_cmd: python3 -m unittest tests.test_hard_gates -v
```

## Red-proof
- red_cmd: evidence_pack_required test fails before hard_gates change
- green_cmd: full test_hard_gates green

## Traceability
| AC | Test |
|----|------|
| AC-1 missing fails | test_evidence_pack_required_for_code |
| AC-2 thin fails | test_evidence_pack_thin_fails |
| AC-3 prose skips | test_prose_skips_evidence_pack |
| AC-4 template/skill | templates/PR_DRAFT.md + release_mgmt |

## Threat notes
- Asset: PR score / release trust
- Abuse: fake thin evidence — require ≥2 known tokens and min body length

## Things that look bad but are actually fine
1. Existing "## Evidence" narrative section remains; hard gate is "## Evidence pack".
2. Token list is keyword-based not machine-parsed CI XML.
3. Does not parse RELEASE_RUNBOOK at pr_review (score-time PR_DRAFT only).
