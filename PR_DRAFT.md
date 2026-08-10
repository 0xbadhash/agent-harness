# PR Draft — HSQ-3 P1 (G3 path tests, G4 red/green, G6 lockfile)

**Spec:** `.agents/specs/HSQ-3-p1-quality-gates.md`
**Version:** 1.4.23

## What Problem This Solves
Ships can add modules without tests, fake TDD narrative, or bump lockfiles without audit.

## Why This Change Was Made
P1 gates from quality plan — fail closed on disk evidence.

## User Impact
- Changed source paths need tests or Untested paths waiver
- red_cmd must fail / green_cmd must pass when declared
- Lockfile diffs trigger available auditors

## Red-proof
- red_cmd: `false`
- green_cmd: `true`
- Also unit tests for G4 AC-4/AC-5

## Traceability
| AC | Test |
|----|------|
| AC-1 | tests/test_hsq3_p1_gates.py::TestPathTests::test_ac_1_missing_test |
| AC-2 | tests/test_hsq3_p1_gates.py::TestPathTests::test_ac_2_untested_waiver |
| AC-3 | tests/test_hsq3_p1_gates.py::TestLockAudit::test_ac_3_no_lockfile |
| AC-4 | tests/test_hsq3_p1_gates.py::TestRedGreen::test_ac_4_red_must_fail |
| AC-5 | tests/test_hsq3_p1_gates.py::TestRedGreen::test_ac_5_tdd_na |
| AC-6 | tests/test_hsq3_p1_gates.py::TestRedGreen::test_ac_6_good_cmds + hard_gates wire |

## Untested paths
| scripts/check_lockfile_audit.py | covered via unit mock of _changed; live npm optional |
| scripts/check_changed_path_tests.py | unit tests TestPathTests |
| scripts/check_red_green_cmds.py | unit tests TestRedGreen |

## Threat notes
- red/green cmds run with timeout 60s, no shell=True
- lockfile audit only when tools present (no false fail offline)

## Evidence pack
- hard_gates path_tests red_green lockfile_audit
- pytest tests/test_hsq3_p1_gates.py
- validate compliance

## Things that look bad but are actually fine
1. npm/pip-audit absence is warn-skip not fail (sandboxes).
2. Path token match is heuristic stem/token not AST import graph.
3. true/false builtins for red/green avoid needing /bin on all OS.
4. Spec waiver docs-only skips path tests.
5. Untested paths table is explicit opt-out for glue scripts.
