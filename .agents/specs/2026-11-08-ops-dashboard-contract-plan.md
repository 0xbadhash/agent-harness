# Plan — document the ops-dashboard contract

Linked spec: `.agents/specs/2026-11-08-ops-dashboard-contract.md`

The git diff crosses the large-ship line because prior review drafts were replaced. The product change is still comment text.

## Approach

Do not change `SuccessExitStatus`, `OnCalendar`, `ExecStart`, user, group, umask, or timer enablement. Say in the unit that exit 2 is an intentional RED under `SuccessExitStatus=0 2`, and that the enabled timer has four calendars: 01:00 UTC, 12:00 UTC, 19:45 UTC, and Sun–Thu 23:45 UTC. Repeat that sentence on the ops-dashboard rows of `agent-tasks/ops/SYSTEMD-TIMERS-INVENTORY.md`.

## Architecture

The base timer file keeps two `OnCalendar=` directives. The other two calendars stay in the existing drop-ins `after-night.conf` and `weekday-0745-hkt.conf`. The installed unit gets the same comments as `deploy/`. A contract test reads the directive lines and `systemctl show`.

## Implementation sequence

1. Add the failing contract test for the service, the timer, and the registry row.
2. Add the comment and description text, then confirm the loaded unit is unchanged.
3. Record spec, review, and this plan. Do not release or push.
