# HSQ-1 — Ship Quality SoT

**Status:** accepted for implement  
**Product:** agent-harness  
**Date:** 2026-08-10

## Goal

Fewer false large-diff flags, durable spec-waiver visibility, honest CI skill-conformance story, portfolio install force + protect drift, and explicit Security IOC ops wiring.

## Acceptance criteria

| ID | AC |
|----|-----|
| AC-1 | `review_scope` thresholds overridable via `product_plugin.yaml` `review_scope:`; defaults unchanged |
| AC-2 | Successful spec waivers append to `.agents/artifacts/WAIVER_LOG.jsonl`; `waiver_report.py` summarizes |
| AC-3 | Daytime CI documents + path-filters skill conformance (checklist already runs) |
| AC-4 | `portfolio_install_report.py --force` reinstalls even when version matches; protect-drift reported |
| AC-5 | Ship-flow / ops docs mention Security IOC as ops (not PR hard gate) |

## Non-goals

a11y gate, perf suite, metrics warehouse, vault flag-day, hard N-waiver/month stop.

## PR stack

1. Configurable thresholds  
2. Waiver ledger  
3. CI skill conformance honesty  
4. Portfolio force + protect drift  
5. IOC docs  
