# PR Draft — night bar surface_inventory hardcodes

**Spec waiver:** chore  
**Version target:** 1.4.37  

## What Problem This Solves
Night readiness FAIL `scripts/surface_inventory.py:33 [external_url] https://artauthenticity.xyz` across products stuck on protected stale `check_hardcodes` (1.4.34) while SoT was 1.4.36+.

## Why This Change Was Made
WINDOW 2 night bar: align install to current harness; fix night runner so stale FAIL cannot recur. No live sites.

## User Impact
- Inventory SoT uses hostnames; scheme applied at runtime
- Night autofix rewrites old https:// literals in product surface_inventory when hardcodes fails on that path
- Portfolio install propagates fixed inventory (not protected)

## Red-proof
- red_cmd: `python3 -c "from pathlib import Path; t=Path('scripts/surface_inventory.py').read_text(); import sys; sys.exit(0 if 'https://artauthenticity.xyz' in t.split('KNOWN_CATALYXT_HOSTS',1)[1].split(')',1)[0] else 1)"`
- green_cmd: `python3 -m unittest tests.test_surface_inventory -v`

## Traceability
| AC | Test / smoke |
|----|--------------|
| AC-1 KNOWN table has no https://artauthenticity literal | tests/test_surface_inventory.py::test_source_has_no_artauthenticity_https_literal |
| AC-2 known_url builds https | tests/test_surface_inventory.py::test_known_url_builds_https |
| AC-3 merge still emits https URLs | tests/test_surface_inventory.py::test_merge_includes_known |
| AC-4 night autofix clears old scanner FAIL | night_shift_autofix.try_fix_surface_inventory_hardcodes |
| smoke | python3 -m unittest tests.test_surface_inventory -v |

## Threat notes
- authz: none
- secrets: inventory hosts are public CEO list, not credentials
- abuse: autofix only rewrites known CEO host tuple https→hostname

## Evidence pack
| Item | Result |
|------|--------|
| hard_gates | pr_validator |
| unittest | tests/test_surface_inventory.py |
| dry proof | old scanner + new inventory EXIT 0; autofix on old inventory EXIT 0 |

## Things that look bad but are actually fine
1. Does not reopen 1.4.35 trait gates or 1.4.36 kanban writer ship
2. Night-bar 73c2221 stays unpushed
3. Leftover MORNING_TRIAGE / NIGHT_SHIFT_* / ops_dashboard left unstaged
4. check_hardcodes remains protect-listed on products — inventory fix does not need scanner overwrite
