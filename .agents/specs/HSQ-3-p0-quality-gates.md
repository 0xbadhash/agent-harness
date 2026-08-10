# HSQ-3 P0 — Ship quality gates (AC map, secrets, diff compile)

**Status:** accepted for implement  
**Product:** agent-harness  
**Date:** 2026-08-10  
**Version target:** 1.4.22

## Goal

Fail-closed gates that reduce bugs / improve spec fidelity / security **without** session-OS drift. Disk + tests are truth.

## Items

| ID | Gate |
|----|------|
| G1 | AC executable map — every AC-n in linked spec mapped in Traceability and present in tests (or N/A) |
| G5 | Tighten secrets regex on added lines (JWT, sk-, npm_, AIza, long bearer) |
| G14 | Diff-scoped compile — `py_compile` every changed `.py` on ship range |

## AC

| ID | Criterion |
|----|-----------|
| AC-1 | `check_ac_traceability` fails when AC-1 in spec has no test reference and no N/A |
| AC-2 | `check_ac_traceability` passes when AC mapped to `test_ac_1` or tests mention AC-1 |
| AC-3 | Secrets regex fails on added line containing JWT-shaped or `sk-` live-looking token |
| AC-4 | Secrets clean on normal code without those patterns |
| AC-5 | `check_diff_compile` fails on syntax-invalid changed `.py` |
| AC-6 | hard_gates wires G1+G14 for non-prose; G5 via existing secrets path |

## Out of scope

Session duration gates, auto-compact policy, Clepsydre UI.
