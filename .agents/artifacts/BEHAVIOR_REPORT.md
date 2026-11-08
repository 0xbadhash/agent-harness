# BEHAVIOR-REPORT

**Marker:** BEHAVIOR-REPORT
**Contract:** .agents/artifacts/BEHAVIOR_CONTRACT.md
**Target:** host systemd timers and config/night_shift_products.yaml

## Results

| Clause | Status | Evidence |
|--------|--------|----------|
| 1. Only night-shift-all is scheduled | pass | `systemctl list-timers --all 'night-shift*'` listed one timer: night-shift-all.timer, next 2026-11-08 19:15 UTC, last success 2026-11-07 19:15 UTC |
| 2. Survivor is enabled | pass | `systemctl is-enabled night-shift-all.timer` printed `enabled` |
| 3. Duplicate unit is not installed | pass | `systemctl is-enabled night-shift-readiness.timer` printed `not-found`. Both `/etc/systemd/system/night-shift-readiness.timer` and `.service` are absent |
| 4. Watchlist stays registered | pass | `config/night_shift_products.yaml` contains the line `watchlist: ~/watchlist` |
| 5. A second retire leaves the survivor | pass | The retire command printed `remove=[]` and exit 0. `/etc/systemd/system/night-shift-all.timer` was still present afterward |

## Summary

- pass: 5 · fail: 0 · blocked: 0
- NEXT_SKILL=/pr_review --validate
