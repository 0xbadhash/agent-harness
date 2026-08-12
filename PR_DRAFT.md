# PR Draft — test-trigger schedule in OPS + night-shift-log

**Spec waiver:** chore  
**Version target:** 1.4.27  
**Range:** cb21214...HEAD (#15 already on main; release closeout)

## What Problem This Solves
Operators could not see when ship / CI / night / code-review tests fire from Obsidian alone.

## Why This Change Was Made
Wire single schedule SoT into OPS-DASHBOARD and every night-shift-log.

## User Impact
- OPS shows full act map after each dashboard refresh  
- Product night-shift-log includes compact schedule  
- Night readiness reports add “When else” column  

## Red-proof
- red_cmd: `false`
- green_cmd: `true`
- TDD: unit tests for schedule_markdown content

## Traceability
| AC | Evidence |
|----|----------|
| Schedule embed OPS | ops_dashboard.py + live OPS section |
| Schedule embed night log | night_shift_log.py + vault logs |
| Night gate when-else | night_shift_readiness.py |
| Unit | tests/test_test_trigger_schedule_mod.py |

## Threat notes
- authz: N/A (docs/ops UI text only)
- secrets: gitleaks clean on range

## Evidence pack
- hard_gates / pr_validator
- pytest 188
- secrets clean

## Things that look bad but are actually fine
1. Spec waiver chore — docs/ops wire-in, not product feature AC set.
2. GitHub daytime still not scraped into OPS fail rows (by design; act rule says open Actions).
3. Schedule is static — not live CI status.
4. Night log rewrite of history entries only adds schedule header once.
5. Portfolio install may lag product HARNESS_VERSION until force reinstall.

## Cross-review
See `.agents/artifacts/CROSS_REVIEW.md` — blockers=0.
