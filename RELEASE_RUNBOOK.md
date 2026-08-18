# RELEASE_RUNBOOK — agent-harness v1.4.31

**Score:** 100 · shipped · 2026-08-18

## Proof (before done)

| Metric | jobs=1 | jobs=10 |
|--------|--------|---------|
| products | 10 | 10 |
| wall | 13.0s | 5.2s (later 5.2s) / recheck 13.0s vs children-aware |
| cpu_self+children | 12.5s | 13.0s |

Dry-run `--quick`: wall drops ~13s→~5s; CPU≈sum of children; list unchanged (10 ids).

## Smoke
hardcodes + unit pass. No stamp/comet/Playwright in this ship.

## Rollback
git checkout v1.4.30

## §9
1. bip39lab dry-run FAIL not reopened as product PASS
2. Optional skills still installed if present
3. ZAP HTML kept; SUMMARY for ops
