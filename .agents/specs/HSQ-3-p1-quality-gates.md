# HSQ-3 P1 — Changed-path tests, lockfile audit, red/green cmds

**Status:** accepted for implement  
**Product:** agent-harness  
**Version target:** 1.4.23  
**Date:** 2026-08-10

## Items

| ID | Gate |
|----|------|
| G3 | Changed product modules must have a test reference or explicit Untested waiver |
| G6 | Lockfile changes → npm audit / pip-audit when tool available (fail high when available) |
| G4 | red_cmd / green_cmd in PR_DRAFT must be runnable (or TDD N/A) |

## AC

| ID | Criterion |
|----|-----------|
| AC-1 | G3 fails when `scripts/foo.py` added with no test importing/mentioning foo |
| AC-2 | G3 passes with `## Untested paths` listing the file + reason |
| AC-3 | G6 skips clean when no lockfile in diff |
| AC-4 | G4 fails when red_cmd exits 0 (should fail) for explicit test fixtures |
| AC-5 | G4 accepts TDD N/A docs-only wording |
| AC-6 | hard_gates wires G3/G4 for non-prose; G6 when lockfiles change |
