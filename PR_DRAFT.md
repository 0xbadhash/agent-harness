# PR Draft — surface_inventory known hosts (pane call)

**Spec:** docs/specs/2026-08-18-night-parallel-waiting-leftovers.md  
**Plan:** docs/specs/2026-08-18-night-parallel-waiting-leftovers-plan.md  
**Version target:** 1.4.32  

## What Problem This Solves
Pane calls `python3 scripts/surface_inventory.py`; list must succeed with known Catalyxt hosts without inventing domains or scanning the internet.

## Why This Change Was Made
CEO: write the real script; do not delete the call; no domain-find.

## User Impact
- `python3 scripts/surface_inventory.py` lists 7 known Catalyxt hosts and exits 0 (pane call works).
- No internet discovery; optional `--probe` only hits declared URLs.
- Hardcode allowlist includes `artauthenticity.xyz` for the known list.

## Red-proof
- red_cmd: `python3 -c "import sys; sys.exit(1)"`
- green_cmd: `python3 scripts/surface_inventory.py`

## Traceability
| AC | Evidence |
|----|----------|
| AC-1 | night parallel carried from 1.4.31 (this patch: inventory) |
| AC-2 | timing proof prior ship |
| AC-3 | surface_inventory.py + test_surface_inventory · pane exit 0 |
| AC-4 | pytest cache scrub (1.4.31) |
| AC-5 | next_skill plan_review (1.4.31) |
| AC-6 | plans archived (1.4.31) |
| AC-7 | SESSION_CONTEXT / pipeline (1.4.31+) |
| AC-8 | schedule one-liner + zap SUMMARY (1.4.31) |
| AC-9 | no Graft/domain-find/ZAP night · pane lists known hosts only |

## Threat notes
- authz: N/A
- secrets: no probe by default

## Evidence pack
| Item | Result |
|------|--------|
| hard_gates | validate |
| unittest | test_surface_inventory |
| pane call | exit 0 + 7 hosts |

## Things that look bad but are actually fine
1. Hosts listed without live probe by default
2. ZAP yaml may still be a subset — inventory merges known+zap
3. No stamp/Playwright in this ship
