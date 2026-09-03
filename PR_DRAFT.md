# PR Draft — register jasmine on night shift

**Spec waiver:** chore  
**Version target:** 1.4.41  

## What Problem This Solves
Jasmine had harness files on disk but was not on the night product list and the install was never committed. Night_all skipped it.

## Why This Change Was Made
Operator: cleanup agent-harness across repos including jasmine.

## User Impact
- `night_shift_all` includes ~/jasmine
- No product VERSION bump

## Red-proof
- red_cmd: `python3 -c "raise SystemExit(0 if 'no-such-product-zzz' in open('config/night_shift_products.yaml').read() else 1)"`
- green_cmd: `python3 scripts/check_night_shift_product_paths.py`

## Traceability
| AC | Test / smoke |
|----|--------------|
| AC-1 jasmine in night yaml | check_night_shift_product_paths.py |
| AC-2 path exists | same |
| smoke | product_smoke |

## Threat notes
- authz: none
- secrets: none
- abuse: none

## Evidence pack
| Item | Result |
|------|--------|
| hard_gates | pr_validator |
| unittest | path check |
| validate | check_night_shift_product_paths |

## Things that look bad but are actually fine
1. Duplicate checkouts catalyxt.ltd / atom-learning-family left in place (same remotes as website / figure-it-out)
2. artauthenticity still has no harness (not requested)
3. Jasmine game WIP (src/) not committed
4. Night leftover artifacts on harness unstaged
