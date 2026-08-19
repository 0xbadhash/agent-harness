# PR Draft — release origin fail-closed push gate

**Spec waiver:** chore  
**Version target:** 1.4.34  

## What Problem This Solves
Releases could land locally tagged but unpushed (Figure/watchlist class). Same miss must not land twice.

## Why This Change Was Made
CEO: /release_mgmt must auto-push HEAD + v$VERSION and fail closed if origin lacks them.

## User Impact
- Product ships: finish_ship --require-push pushes then verifies ls-remote
- Gate command: `python3 scripts/release_origin_gate.py --push` / `finish_ship.py --require-push`

## Red-proof
- red_cmd: `python3 scripts/release_origin_gate.py --verify-only --expect-tag v0.0.0-missing-dry-miss`
- green_cmd: `python3 -m unittest tests.test_release_origin_gate -v`

## Traceability
| AC | Test / smoke |
|----|--------------|
| AC-1 Auto-push HEAD + tags when --require-push | tests/test_release_origin_gate.py (push_head_and_tags) + scripts/finish_ship.py --require-push |
| AC-2 Fail-closed if origin lacks HEAD or v$VERSION | tests/test_release_origin_gate.py (verify miss) + red_cmd dry miss EXIT 1 |
| AC-3 release_mgmt skill mandates origin gate | skills/release_mgmt/SKILL.md step 9 |
| smoke | python3 -m unittest tests.test_release_origin_gate -v |

## Threat notes
- authz: uses existing git remotes/credentials; push only to configured origin
- secrets: none logged; relies on ambient git credentials
- abuse: forged tag names rejected by expect-tag / VERSION binding

## Evidence pack
| Item | Result |
|------|--------|
| hard_gates | pr_validator --update-pipeline |
| unittest | tests/test_release_origin_gate.py |
| red/green | dry miss EXIT 1; unittest green |
| validate | scripts/hard_gates.py + pr_validator |

## Things that look bad but are actually fine
1. Night-bar commit 73c2221 stays unpushed (branched from origin/main)
2. No stamp/Playwright in this ship
3. Portfolio broadcast after harness gate tags — separate step
