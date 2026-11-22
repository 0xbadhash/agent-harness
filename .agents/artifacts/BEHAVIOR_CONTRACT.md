# Behavior contract — ops-dashboard documentation

**Marker:** BEHAVIOR-CONTRACT

Operator-visible checks. Do not read the git diff to score these.

1. `systemctl show ops-dashboard.service -p SuccessExitStatus` prints `SuccessExitStatus=0 2`.
2. `systemctl is-enabled ops-dashboard.timer` prints `enabled`.
3. `systemctl show ops-dashboard.timer -p TimersCalendar` lists four calendars: 01:00 UTC, 12:00 UTC, 19:45 UTC, and 23:45 UTC.
4. `systemctl cat ops-dashboard.service` contains the phrase `intentional RED` and still contains `SuccessExitStatus=0 2`.
5. `systemctl cat ops-dashboard.timer` contains `four` and the four clock times above.
6. The registry file `agent-tasks/ops/SYSTEMD-TIMERS-INVENTORY.md` contains `intentional RED` and `SuccessExitStatus=0 2` on the ops-dashboard rows.

# Behavior contract — root IoC real homes (2026-11-22)

**Marker:** BEHAVIOR-CONTRACT
**Target:** CLI `scripts/security_root_ioc_scan.py`
**Setup:** `PRODUCT_VAULT_ROOT` pointed at an empty temp directory. No live vault write intended.

## User tasks

1. As the operator, `HOME=/root` `--print-roots --no-artifact` lists each directory under `/home` as required and does not print `status=ok`.
2. As the operator, `--home` to a missing path exits 2 with `status=incomplete`.
3. As the operator, `--home` to an unlistable directory exits 2 and does not report a pin count above 0.
4. As the operator, `--home` to a tree containing `keyv@6.0.0` exits 1 with `status=fail`.
5. As the operator, `--home` to an empty readable directory exits 0 with `status=ok`.

## Must not

- Print `required /home` as its own line when children exist.
- Write a vault artifact when `--no-artifact` is set.
