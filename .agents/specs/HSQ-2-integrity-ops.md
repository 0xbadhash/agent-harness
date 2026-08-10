# HSQ-2 — Integrity & Ops Hardening

**Status:** accepted for implement  
**Product:** agent-harness  
**Date:** 2026-08-10  
**Version target:** 1.4.21

## Items 1–9

1. FSM legal transitions (+ `--force-transition` + log)
2. Auto-marker ship-chain documentation + `--allow-auto-markers` flag
3. Real CI skill-conformance path filter
4. Vault defaults without hardcoded `/opt` as primary
5. Protect-list merge playbook doc
6. Waiver counts on OPS-DASHBOARD
7. Ops JSONL daily snapshots
8. CODE-REVIEW quality floors (min content)
9. `--skip-hard-gates` audit trail

## AC

| ID | Criterion |
|----|-----------|
| AC-1 | Illegal phase jump raises; force logs SKIP_HARD_GATES-style trail |
| AC-2 | run_ship_chain requires `--allow-auto-markers` for stub artifacts; docs warn |
| AC-3 | skill-conformance CI skips when no skill-relevant paths (non-main PR) |
| AC-4 | Scripts prefer env/plugin; `/opt` only last-resort with stderr warn |
| AC-5 | `docs/protect-list-merge.md` playbook exists |
| AC-6 | OPS-DASHBOARD shows waiver 30d summary when log present |
| AC-7 | ops_dashboard appends JSONL snapshot under vault or harness artifacts |
| AC-8 | CODE-REVIEW fails if body shorter than floor (non-auto-marker path) |
| AC-9 | skip-hard-gates appends SKIP_HARD_GATES_LOG.jsonl |
