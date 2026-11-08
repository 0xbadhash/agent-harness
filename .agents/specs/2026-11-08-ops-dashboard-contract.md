# Ops dashboard exit-2 and four-calendar contract

- **Product:** agent-harness
- **Created:** 2026-11-08
- **Status:** ready-for-agent
- **Priority:** P1
- **Roadmap:** CHANGELOG.md → this docs slice (no generator change)
- **Plan:** none
- **Tracker:** local
- **Constitution:** AGENTS.md + `.agents/policy/base_constraints.md`
- **Grill-me:** complete

## Problem Statement

Operators see `ops-dashboard.service` exit 2 and a systemd result of success. The timer description still says morning plus midday UTC. The live timer is already enabled and already has four calendars. The mismatch reads like a failed or half-installed job.

## Solution

The unit text and the ops-dashboard registry row say the same contract: exit 2 is an intentional RED under `SuccessExitStatus=0 2`, and the timer stays enabled with four calendars. Nothing in the schedule, the exit status list, or the writer changes.

## User Stories

1. As an operator, I want the service unit to say that exit 2 means the dashboard overall is RED, so a successful systemd result is not mistaken for a green dashboard.
2. As an operator, I want the timer unit to name all four calendars, so the morning-plus-midday description is not the only schedule I see.
3. As an operator, I want the registry row to match that unit text, so the inventory is not still a two-calendar capture.

## Implementation Decisions

- Surfaces: `deploy/ops-dashboard.service`, `deploy/ops-dashboard.timer`, the installed copies under `/etc/systemd/system/`, and the ops-dashboard rows in `vault/agent-tasks/ops/SYSTEMD-TIMERS-INVENTORY.md`.
- `SuccessExitStatus=0 2` stays. Base `OnCalendar` lines stay `*-*-* 01:00:00 UTC` and `*-*-* 12:00:00 UTC`. Drop-in calendars stay `*-*-* 19:45:00 UTC` and `Sun,Mon,Tue,Wed,Thu *-*-* 23:45:00 UTC`.
- The timer stays enabled. `ExecStart`, user, group, umask, and drop-in hooks stay as they are. The live unit's `Group=secondbrain` and the repo unit's `Group=debian` are not reconciled.
- `scripts/ops_dashboard.py` is out of this slice. It already returns 2 when overall is RED (`return 0 if d.overall != "RED" else 2`).

## Testing Decisions

- Public contract is the unit text plus the registry row, checked by `tests/test_ops_dashboard_contract.py`.
- Live proof is `systemctl show` for `SuccessExitStatus`, `UnitFileState=enabled`, and the four `TimersCalendar` values, before and after a comment-only daemon-reload.
- Do not run `ops_dashboard.py --write`. That would rewrite the vault dashboard.

## Acceptance Criteria

- [ ] AC-1: the service unit documents that exit 2 is an intentional RED and still contains exactly `SuccessExitStatus=0 2`.
- [ ] AC-2: the timer unit documents that it is enabled with four calendars (01:00, 12:00, 19:45, and Sun–Thu 23:45 UTC) while the base file still has exactly those two `OnCalendar=` directives.
- [ ] AC-3: the registry entry (ops-dashboard rows in `agent-tasks/ops/SYSTEMD-TIMERS-INVENTORY.md`) states the same exit-2 and four-calendar contract.
- [ ] AC-4: after the text change, the loaded unit is still enabled, `SuccessExitStatus` is still `0 2`, and the loaded calendars are still those four.

## Out of Scope

- Changing exit codes, `SuccessExitStatus`, `OnCalendar` values, `Persistent`, `RandomizedDelaySec`, `ExecStart`, user, group, or umask.
- Enabling, disabling, or restarting the timer.
- Editing `ops_dashboard.py` or its existing tests.
- Rewriting `Fleet-Dashboard.md` (row V11 already lists the four times).
- Pushing, tagging, or releasing.

## Grill-me

**Status:** complete
**Date:** 2026-11-08

The session has no separate operator. Answers are the consensus instruction. Recommended defaults are logged.

### G1 Outcome
- Q: What does done look like in one sentence?
  - A: An operator can read the unit and the registry row and see that exit 2 is an intentional RED under SuccessExitStatus=0 2, and that the timer is enabled with four calendars.
  - Recommended was: document that contract and leave the running timer alone.

### G2 Non-goal / kill
- Q: What must this change not do?
  - A: It must not change exit codes, SuccessExitStatus, calendars, enablement, ExecStart, or the dashboard writer. Cancel the slice if the only way to "fix" exit 2 is to make systemd fail the timer.
  - Recommended was: comments and the registry row only.

### G3 Wrong product
- Q: Is the dashboard script the right surface?
  - A: No. The script already returns 2 for overall RED. The wrong text is the unit description and the inventory row that still lists two calendars. The script file is dirty with unrelated work and stays untouched.
  - Recommended was: unit plus registry, not the generator.

### G4 Cheapest alternative
- Q: What is the smallest ship that still removes the ambiguity?
  - A: Comment and description text in the unit, the same sentence on the registry row, and a test that the directives did not change.
  - Recommended was: docs-only contract, no new calendar lines.

### G5 Abuse / failure
- Q: How does a bad edit of this contract fail?
  - A: Removing 2 from SuccessExitStatus turns an intentional RED into a timer failure. Adding or dropping a calendar changes when the dashboard is written. The test locks the directive lines. Documentation must not copy dashboard contents or secrets.
  - Recommended was: fail closed on any directive change.

### G6 Verify
- Q: How do we prove it before calling the slice done?
  - A: The contract test fails before the sentences exist and passes after. `systemctl show` still reports SuccessExitStatus=0 2, UnitFileState=enabled, and the same four calendars.
  - Recommended was: pytest plus systemctl show, no --write.

### G7 Priority / delay
- Q: Why document this now instead of leaving the units as they are?
  - A: The 2026-11-08 run exited 2 and was reported as success. The description still says morning plus midday. The consensus was to standardize that text now, with no behaviour change.
  - Recommended was: do it in this item, do not widen into a generator rewrite.

## Clarifications

### 2026-11-08
- Q: Which file is the registry entry?
  - A: The ops-dashboard rows in `/opt/second-brain/vault/agent-tasks/ops/SYSTEMD-TIMERS-INVENTORY.md`. The 2026-10-20 capture listed only the base unit's two calendars. Drop-ins already add 19:45 UTC and Sun–Thu 23:45 UTC. Fleet-Dashboard V11 already lists the four times and is not rewritten. The dated evidence dump under `/var/lib/pilot/rebuild-sot-systemd-20261020/` stays a historical capture.

## Further Notes

Live `Group=secondbrain` versus repo `Group=debian` is pre-existing. Reconciling it would change the installed unit. It stays out of scope.

## Handoff

- Next: `/execute_dev` (contract text only; TDD on the unit and registry strings)
- Then: `/code_review` → follow `NEXT_SKILL` → `/pr_review --validate`
- Do not `/release_mgmt` (it tags and pushes).
