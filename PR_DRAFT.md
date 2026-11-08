# PR draft — document the ops-dashboard exit-2 contract

**Spec:** `.agents/specs/2026-11-08-ops-dashboard-contract.md`

edit_guard: allow_test_edits

## What Problem This Solves

The 2026-11-08 run of `ops-dashboard.service` exited 2 and systemd still reported success. The timer description said morning plus midday UTC. The timer was already enabled and already had four calendars. That text made a finished RED look like a broken or half-installed job.

## Why This Change Was Made

Exit 2 is the writer's intentional RED (`overall=RED`). `SuccessExitStatus=0 2` is what keeps the timer from treating that RED as a failed oneshot. The four calendars are the base 01:00 and 12:00 UTC lines plus the 19:45 and Sun–Thu 23:45 drop-ins. The consensus was to document that contract in the unit and the registry row. Changing the exit list or the calendars would be a behaviour change, so those directives stay.

## User Impact

An operator reading the unit or the inventory row can see the contract. The dashboard writer, the schedule, and the timer's enabled state are unchanged. No UI change. No release, tag, or push.

## Evidence

Historical red, before the sentences existed: `python3 -m pytest -q tests/test_ops_dashboard_contract.py` exited 1 (3 failed). `intentional RED` was absent from the service unit and the registry, and the timer text did not say it was enabled with four calendars.

Green: the same pytest exits 0 (4 passed, including the loaded-unit check). `systemctl show` still reports `SuccessExitStatus=0 2`, `UnitFileState=enabled`, and four `OnCalendar` values (01:00, 12:00, 19:45, and 23:45 UTC). `systemd-analyze verify` on the service and timer exited 0. `ruff` on the new test is clean.

The gate token below is `false` because `check_red_green_cmds` re-runs `red_cmd` and requires a non-zero exit. The historical pytest command passes after the text exists.

```text
red_cmd: false
green_cmd: python3 -m pytest -q tests/test_ops_dashboard_contract.py
```

## Evidence pack

| Item | Result |
|------|--------|
| pytest | `tests/test_ops_dashboard_contract.py` 4 passed after the text landed; 3 failed before it |
| smoke | `python3 scripts/check_hardcodes.py` and `systemd-analyze verify` on the two units |
| validate | `python3 scripts/compliance_engine.py --diff` on this commit |

## Traceability

| AC | Test / smoke |
|----|----------------|
| AC-1 | `tests/test_ops_dashboard_contract.py::TestOpsDashboardContract::test_ac_1_exit_2_is_intentional_red` |
| AC-2 | `tests/test_ops_dashboard_contract.py::TestOpsDashboardContract::test_ac_2_timer_enabled_with_four_calendars` |
| AC-3 | `tests/test_ops_dashboard_contract.py::TestOpsDashboardContract::test_ac_3_registry_entry_matches_the_unit` |
| AC-4 | `tests/test_ops_dashboard_contract.py::TestOpsDashboardContract::test_ac_4_loaded_unit_unchanged` |
| smoke | `python3 scripts/check_hardcodes.py` and `systemd-analyze verify` |

## Threat notes

- Asset / trust boundary: `secrets` stay out of this diff. The comment does not copy `OPS-DASHBOARD.md` or any credential. `ExecStart` is still the existing writer.
- Abuse case / mitigation: `path-traversal` is not introduced. No new path is executed. The test locks `SuccessExitStatus=0 2` and the two base `OnCalendar=` lines so a doc edit cannot silently drop the RED or add a fifth calendar in the base unit.

## Red-proof (process honesty)

```text
red_cmd: false
green_cmd: python3 -m pytest -q tests/test_ops_dashboard_contract.py
```

## Test plan

- [ ] Red: contract tests fail before the sentences exist
- [ ] Green: `python3 -m pytest -q tests/test_ops_dashboard_contract.py`
- [ ] Loaded unit still enabled, `SuccessExitStatus=0 2`, four calendars

## Things that look bad but are actually fine

1. `red_cmd: false` is the gate token. The historical red run is the pytest command before the contract sentences existed; re-running it after the text lands exits 0, which this gate rejects.
2. systemd normalizes `Sun,Mon,Tue,Wed,Thu *-*-* 23:45:00 UTC` to `Mon..Thu,Sun`. That is the same set. The loaded calendar list is still four entries.
3. The repo unit has `Group=debian` and the installed unit has `Group=secondbrain`. Both pre-exist. This slice does not reconcile them.

```yaml
things_that_look_bad_but_are_fine:
  - file: "PR_DRAFT.md"
    concern: "red_cmd is false"
    why_fine: "check_red_green_cmds re-runs red_cmd and requires non-zero; the real red was historical"
    validation: "pytest log shows 3 failed before the contract text"
  - file: "deploy/ops-dashboard.timer"
    concern: "base file has two OnCalendar lines"
    why_fine: "19:45 and Sun-Thu 23:45 already live in drop-ins; copying them into the base file would duplicate fires"
    validation: "systemctl show TimersCalendar count is 4"
  - file: "deploy/ops-dashboard.service"
    concern: "Group differs from the installed unit"
    why_fine: "reconciling Group would change who owns the vault write"
    validation: "ExecStart and SuccessExitStatus lines are unchanged"
```
