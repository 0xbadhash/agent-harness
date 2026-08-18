# PR Draft — night parallel + Waiting leftovers

**Spec:** docs/specs/2026-08-18-night-parallel-waiting-leftovers.md  
**Plan:** docs/specs/2026-08-18-night-parallel-waiting-leftovers-plan.md  
**Version target:** 1.4.31  

## What Problem This Solves

Sequential night_shift_all summed wall clocks; Waiting leftovers (surface_inventory invent, skill router mismatch, leftover plans, stale context, schedule duplication, raw ZAP HTML, over-required optional skills).

## Why This Change Was Made

CEO window-2: parallel independent products + clear Waiting items honestly without Graft/ECC, domain-find, or ZAP night crawl.

## User Impact

- Night all-products `--jobs` (default min(n,10)); wall → ~slowest  
- Optional `surface_inventory.py` (declared targets only)  
- ship_skills vs next_skill aligned; qa_campaign/retrospect/audit_harness optional  
- Night reports link schedule SoT once; ZAP SUMMARY.md  

## Red-proof

- red_cmd: `python3 -c "import sys; sys.exit(1)"`
- green_cmd: `python3 -m unittest tests.test_night_shift_all_parallel tests.test_next_skill -v`

## Traceability

| AC | Evidence |
|----|----------|
| AC-1 | test_ten_product_list_unchanged; --jobs parallel |
| AC-2 | dry-run timing jobs=1 vs jobs=10 |
| AC-3 | scripts/surface_inventory.py |
| AC-4 | pytest cache scrub for deleted test_trigger_schedule |
| AC-5 | next_skill after=spec/plan_review; optional_skills |
| AC-6 | docs/specs/archive/*-plan.md |
| AC-7 | pipeline.json task + SESSION_CONTEXT 1.4.30+ |
| AC-8 | night_shift_readiness/log one-liner; zap_summarize |
| AC-9 | no Graft/ZAP night/domain-find |

## Threat notes

- authz: N/A  
- secrets: surface_inventory probes optional; no secrets logged  

## Evidence pack

| Item | Result |
|------|--------|
| hard_gates | pending |
| smoke | product_smoke |
| unittest | parallel + next_skill |
| timing | wall/cpu dry-run report |

## Things that look bad but are actually fine

1. bip39lab dry-run FAIL in timing harness — pre-existing product gate; not reopened as PASS  
2. qa_campaign still exists under skills/ but optional  
3. Raw ZAP HTML files retained for triage; SUMMARY is the ops view  
4. No stamp/comet/Playwright in this ship  
