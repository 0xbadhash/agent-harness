# BEHAVIOR-REPORT

- **Target:** `deploy/auto-review-relay.py` CLI and systemd unit surfaces (source-blind)
- **Date:** 2026-11-28

| Clause | Check | Result |
|--------|-------|--------|
| CLI help | `python3 deploy/auto-review-relay.py --help` | `pass` (exits 0, documents `--hook`, `--sweep`, `--watch`, `--digest`, `--dry`) |
| Digest dry-run | `python3 deploy/auto-review-relay.py --digest --dry` | `pass` (exits 0, outputs `DIGEST: auto-review relay ...: seen 0, sent 0, reminders 0, errors 0`, no Signal sent) |
| Live scheduled digest | `systemctl --user status auto-review-relay-digest.service` | `pass` (`2026-11-28 00:00:24 UTC`, `code=exited, status=0/SUCCESS`) |
| Live watch daemon | `systemctl --user status auto-review-relay-watch.service` | `pass` (`active (running)` since `2026-11-27 10:24:59 UTC`) |
