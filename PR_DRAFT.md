# PR Draft — HSQ-3 P2 (G2/G10/G7/G8)

**Spec:** `.agents/specs/HSQ-3-p2-quality-gates.md`
**spec_sha256:** 313c8151c26a1081ee710c2e0a76248996c227a619e5306e491a6a418b912a7e
**Version:** 1.4.24

## What Problem This Solves
Specs can drift mid-ship; waivers can be abused; threat notes theater; auth paths untested.

## Why This Change Was Made
P2 gates from quality plan.

## User Impact
- Spec hash optional pin
- Waiver budget on waiver ships
- Threat tags for runtime
- security_paths plugin hook

## Red-proof
- red_cmd: `false`
- green_cmd: `true`

## Traceability
| AC | Test |
|----|------|
| AC-1 | tests/test_hsq3_p2_gates.py::TestSpecHash::test_ac_1_missing_spec |
| AC-2 | tests/test_hsq3_p2_gates.py::TestSpecHash::test_ac_2_wrong_hash |
| AC-3 | tests/test_hsq3_p2_gates.py::TestSpecHash::test_ac_3_match |
| AC-4 | tests/test_hsq3_p2_gates.py::TestThreatTags::test_ac_4_needs_tags |
| AC-5 | tests/test_hsq3_p2_gates.py (security paths unit) |
| AC-6 | tests/test_hsq3_p2_gates.py::TestSecurityPaths::test_ac_6_no_config |

## Threat notes
- authz: gate scripts do not expand privileges
- secrets: no new credential storage
- injection: shlex-bound cmds from P1 only

## Evidence pack
- hard_gates spec_hash threat_tags security_paths waiver_budget
- pytest tests/test_hsq3_p2_gates.py
- validate compliance

## Things that look bad but are actually fine
1. Threat tags only when runtime surface true.
2. Waiver budget only when PR is a waiver ship.
3. security_paths empty = skip.
4. spec_sha256 optional unless provided.
5. Path matching for security_paths is prefix-based.
