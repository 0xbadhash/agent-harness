# BEHAVIOR-REPORT

**Marker:** BEHAVIOR-REPORT  
**When:** 2026-08-10  

## Behaviors
1. Illegal FSM transition raises ValueError; force path logs JSONL.
2. CODE-REVIEW quality floor rejects thin auto stubs.
3. skip-hard-gates logs SKIP_HARD_GATES_LOG.jsonl.
4. ops_dashboard collects waiver 30d and appends OPS_SNAPSHOTS.jsonl.

## Runtime surface
Scripts/CI only; no new public HTTP surface.

## Result
PASS under unit tests.
