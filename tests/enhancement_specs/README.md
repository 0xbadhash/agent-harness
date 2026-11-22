# 50 enhancement spec-tests — deterministic

CEO directive 2026-11-22: **before implementing the 50 enhancements, implement the 50 tests that specify them.**

## What this is
One deterministic acceptance test per numbered enhancement from
`/home/debian/hermes/profiles/chief-of-staff/reports/50-ENHANCEMENTS-HARNESSES-2026-11-22.md`.

- E01–E25 → `test_agent_harness_e01_e25.py` (agent-harness)
- E26–E50 → `test_workflow_harness_e26_e50.py` (workflow-harness)

## Determinism contract
Every test passes or fails identically on repeated runs: filesystem, AST and
text checks plus offline imports only. **No network, no LLM calls, no sleeps,
no wall-clock comparisons.** A red test is a specification of pending work,
not a flake.

## Red/green semantics
- Red now = the enhancement is not yet implemented (expected for most).
- When enhancement N is implemented, test N must turn green **without being edited**.
- The gate rule for implementation: no enhancement counts as done until its
  test here is green (same red-green discipline as the ship chain).

## Run
```
/home/debian/agent-harness/.venv/bin/pytest /home/debian/harness-enhancement-tests -v
```

The suite lives OUTSIDE both repos on purpose: it must never flip the
harnesses' own CI while the enhancements are pending.
