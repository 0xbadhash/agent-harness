# QA-CAMPAIGN-INVENTORY
**Marker:** QA-CAMPAIGN-INVENTORY  
**Repo:** agent-harness 1.4.40  
**Date:** 2026-09-02  

## Scale
Harness is ~97 Python scripts, 56 test modules, 17 skills — **not** a 200-bug application. Categories without a surface marked out_of_scope. No invented filler bugs.

## Baseline
- `product_smoke.py`: hardcodes + unit PASS
- `unittest discover tests`: smoke_unit PASS (256+ after campaign fixes)
- No long-running app / HTTP API in this repo

## Tally
| | N |
|--|--|
| Found | 3 |
| Fixed | 3 |
| Residual | 0 confirmed in campaign scope |
| Invented | 0 |

## Bugs

| ID | Cat | Summary | Root cause | Fix |
|----|-----|---------|------------|-----|
| QA-1 | correctness | `scripts/test_*.py` treated as tests | `_is_test` used `test_*.py` basename | only `tests/` and `e2e/` |
| QA-2 | correctness | PR_DRAFT mentioning "hotfix" in prose triggered fix-task | substring `hotfix in t` | match `**Spec waiver:** hotfix` or `edit_guard: fix-task` only |
| QA-3 | correctness | green checkpoint skipped review on dirty tree | SHA-only compare | `_dirty()` fails green |

## Matrix (this repo)

| Category | Status |
|----------|--------|
| Unit | exercised + new regressions |
| Integration | scripts only (git/plugin) |
| E2E / UI | out_of_scope (no website; traits.web=false) |
| Contract OpenAPI | out_of_scope |
| Stress/load | out_of_scope (CLI gates, not a service) |
| Performance | out_of_scope |
| Concurrency | out_of_scope (no shared mutable server) |
| Chaos | out_of_scope |
| Security | hardcodes + edit_guard secrets paths; no exploit PoCs |
| Edge | dirty tree, prose "hotfix", helper script names |
| Regression | tests added for QA-1..3 |
| Compatibility | install bootstrap already covered |
| Observability | out_of_scope (no metrics runtime) |
| Resource leak | out_of_scope |
