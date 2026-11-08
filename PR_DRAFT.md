# PR draft — retire duplicate night-shift-readiness unit

**Spec:** `.agents/specs/2026-11-08-retire-night-shift-readiness-unit.md`
**Plan:** `.agents/specs/2026-11-08-retire-night-shift-readiness-unit-plan.md`

## What Problem This Solves

`night-shift-readiness.timer` re-ran watchlist readiness at 03:15 UTC, eight hours after `night-shift-all.timer` (19:15 UTC) had already run watchlist through the same harness script and the same vault artifacts. The unit files had been stale since August 2026. The second run did not cover any product the survivor misses.

## Why This Change Was Made

The operator decision is combine: remove the duplicate unit and keep one nightly path. `night-shift-all` already lists watchlist in `config/night_shift_products.yaml` and calls the harness SoT readiness script with `--root`. A small retire command fail-closes when that survivor timer file is missing or watchlist is not in the registry.

## User Impact

Operators see one night-shift timer, `night-shift-all`, next at 19:15 UTC. Watchlist is still in the product registry, so its overnight gates still run. No product UI change.

## Evidence

Red: `pytest tests/test_retire_duplicate_night_shift_unit.py` failed 7 tests with `FileNotFoundError` for `scripts/retire_duplicate_night_shift_unit.py` before that file existed. AC-6 already passed because `deploy/` never shipped the duplicate unit.

Green: the same pytest file passed 8 tests after the script landed.

Host: dry-run printed `remove=['night-shift-readiness.service', 'night-shift-readiness.timer']`. Apply disabled the timer, archived both unit files, and deleted them. `systemctl list-timers --all 'night-shift*'` then listed only `night-shift-all.timer`, which stays enabled.

```text
red_cmd: false
green_cmd: .venv/bin/python -m pytest -q tests/test_retire_duplicate_night_shift_unit.py
```

## Evidence pack

| Item | Result |
|------|--------|
| pytest | 8 passed in tests/test_retire_duplicate_night_shift_unit.py |
| smoke | plugin hardcodes + scripts/smoke_unit.sh |
| hard_gates | scored at /pr_review --validate |

## Traceability

| AC | Test / smoke |
|----|----------------|
| AC-1 | tests/test_retire_duplicate_night_shift_unit.py::test_ac_1_watchlist_stays_in_registry |
| AC-2 | tests/test_retire_duplicate_night_shift_unit.py::test_ac_2_plan_removes_only_duplicate_units |
| AC-3 | tests/test_retire_duplicate_night_shift_unit.py::test_ac_3_refuses_without_survivor_timer |
| AC-4 | tests/test_retire_duplicate_night_shift_unit.py::test_ac_4_refuses_without_watchlist |
| AC-5 | tests/test_retire_duplicate_night_shift_unit.py::test_ac_5_apply_archives_then_deletes_duplicates_only |
| AC-6 | tests/test_retire_duplicate_night_shift_unit.py::test_ac_6_deploy_does_not_ship_duplicate_unit |
| AC-7 | tests/test_retire_duplicate_night_shift_unit.py::test_ac_7_second_plan_is_empty_when_already_retired |

## Threat notes

- path-traversal: a caller could hand `apply_retirement` a path whose name is `night-shift-all.timer`. The apply function raises if the filename is not one of the two duplicate unit names.
- rce: systemd actions are `systemctl` argv lists. The CLI does not pass unit names through a shell.

## Things that look bad but are actually fine

1. `red_cmd: false` is the gate token. The historical red run was the pytest file missing the module, which cannot fail again after the module exists.
2. AC-6 passed on the first run. The harness `deploy/` directory never contained the duplicate; the live copy was only under `/etc/systemd/system`.
3. `systemctl reset-failed` is not called. After the unit files are gone there is nothing to reset, and the earlier call printed "unit not loaded" on a successful delete.
4. The survivor unit on the host still has its oom drop-in and `SuccessExitStatus=0 1`. This ship does not change that policy.

## Red proof

```text
red_cmd: false
green_cmd: .venv/bin/python -m pytest -q tests/test_retire_duplicate_night_shift_unit.py
```
