# Plan: Night parallel + Waiting leftovers

- **Spec:** docs/specs/2026-08-18-night-parallel-waiting-leftovers.md
- **Product:** agent-harness
- **Created:** 2026-08-18
- **Status:** ready-for-agent

## Approach

Parallelize night_shift_all product loop; clear Waiting leftovers with honest wiring (no Graft, domain-find, or ZAP night crawl).

## Architecture decisions

- ThreadPoolExecutor around existing `run_one` subprocesses
- surface_inventory optional declared-only
- Demote qa_campaign/retrospect/audit_harness to optional_skills
- Schedule one-liner in night reports; zap_summarize for HTML dumps

## Implementation sequence

1. Parallel --jobs + wall/cpu timing in bin/night_shift_all_products.py
2. Waiting leftovers (inventory, router, archive plans, context, schedule, ZAP summary, optional skills)
3. Spec/tests/ship closeout 1.4.31

## Testing plan

- unittest parallel list + next_skill routes
- dry-run --quick jobs=1 vs jobs=10 wall/cpu
