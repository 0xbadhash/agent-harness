# Behavior contract — ops-dashboard documentation

**Marker:** BEHAVIOR-CONTRACT

Operator-visible checks. Do not read the git diff to score these.

1. `systemctl show ops-dashboard.service -p SuccessExitStatus` prints `SuccessExitStatus=0 2`.
2. `systemctl is-enabled ops-dashboard.timer` prints `enabled`.
3. `systemctl show ops-dashboard.timer -p TimersCalendar` lists four calendars: 01:00 UTC, 12:00 UTC, 19:45 UTC, and 23:45 UTC.
4. `systemctl cat ops-dashboard.service` contains the phrase `intentional RED` and still contains `SuccessExitStatus=0 2`.
5. `systemctl cat ops-dashboard.timer` contains `four` and the four clock times above.
6. The registry file `agent-tasks/ops/SYSTEMD-TIMERS-INVENTORY.md` contains `intentional RED` and `SuccessExitStatus=0 2` on the ops-dashboard rows.
