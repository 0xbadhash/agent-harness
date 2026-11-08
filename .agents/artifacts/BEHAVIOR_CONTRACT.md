# Behavior contract — one nightly readiness timer

**Marker:** BEHAVIOR-CONTRACT

1. `systemctl list-timers --all 'night-shift*'` shows `night-shift-all.timer` and does not show `night-shift-readiness.timer`.
2. `night-shift-all.timer` is enabled.
3. `night-shift-readiness.timer` is not installed.
4. The product registry still contains a `watchlist` id.
5. Running the retire command again does not remove `night-shift-all.timer`.
