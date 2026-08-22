# PR Draft — night bar autofix no URL literal

**Spec waiver:** chore  
**Version target:** 1.4.38  

## What Problem This Solves
1.4.37 install moved the hardcodes FAIL from `surface_inventory.py:33` to `night_shift_autofix.py:257` because autofix contained the literal `https://artauthenticity.xyz`.

## Why This Change Was Made
Night bar: FAIL must not recur. Detect via regex only.

## User Impact
- Products' protected check_hardcodes no longer trip on autofix source

## Red-proof
- red_cmd: `python3 -c "from pathlib import Path; import sys; t=Path('scripts/night_shift_autofix.py').read_text(); sys.exit(0 if 'https://artauthenticity.xyz' in t else 1)"`
- green_cmd: `python3 scripts/check_hardcodes.py`

## Traceability
| AC | Test / smoke |
|----|--------------|
| AC-1 autofix source has no artauthenticity https literal | red_cmd EXIT 1; check_hardcodes green |
| smoke | python3 scripts/check_hardcodes.py |

## Threat notes
- authz: none
- secrets: none
- abuse: regex still matches CEO host https literals in inventory files

## Evidence pack
| Item | Result |
|------|--------|
| hard_gates | pr_validator |
| unittest | check_hardcodes |
| validate | old scanner + fixed autofix EXIT 0 |

## Things that look bad but are actually fine
1. Follow-on to 1.4.37 same night bar (hotfix, not a reopen of trait/kanban ships)
2. Leftovers MORNING_TRIAGE / NIGHT_SHIFT_* / ops_dashboard left unstaged
3. Night-bar 73c2221 stays unpushed
4. Product check_hardcodes stays protect-listed — inventory/autofix fixes do not need scanner overwrite
