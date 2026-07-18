# RELEASE RUNBOOK — agent-harness v1.3.2

**Date:** 2026-07-18  
**Tag:** v1.3.2  
**Version:** `v1.3.2`  
**Theme:** Vault dev-log newest-first + UTC/HKT  
**Scope:** prepend entries; dual-zone When; night_shift day dedupe; product script reinstall  

## Smoke

| Check | Result |
|-------|--------|
| hardcodes | PASS |
| validate full | PASS 4/4 |
| pytest format + kanban | PASS |
| live vault prepend | PASS |

## Pipeline

pr_review 100% → approved → shipped

## Things that look bad but are actually fine

1. Historical vault rows stay old order until rewritten.
2. Product copies updated by commit (not full install_into_product).
3. HKT is Asia/Hong_Kong display only.
