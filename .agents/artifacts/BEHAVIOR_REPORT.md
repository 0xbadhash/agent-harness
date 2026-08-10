# BEHAVIOR-REPORT

**Marker:** BEHAVIOR-REPORT  
**When:** 2026-08-10  
**Runtime:** CLI scripts (check_ac_traceability, check_diff_compile, check_secrets_diff)

## Scenarios

1. Feature PR with unmapped AC → hard_gates fail AC map.
2. Added sk- / JWT line → secrets fail closed.
3. Syntax-invalid changed .py → diff_compile fail.

## Verdict

Behavior matches HSQ-3 P0 AC-1..AC-6 intent.
