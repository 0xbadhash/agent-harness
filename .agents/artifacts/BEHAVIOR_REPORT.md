# BEHAVIOR-REPORT

- **Target:** `deploy/auto-review-relay.py` CLI and tmux watcher surface (source-blind)
- **Date:** 2026-11-28

| Clause | Check | Result |
|--------|-------|--------|
| CLI help | `python3 deploy/auto-review-relay.py --help` | `pass` (exits 0) |
| Digest dry-run | `python3 deploy/auto-review-relay.py --digest --dry` | `pass` (exits 0, no Signal sent) |
| Claude & Codex watch dry-run | `python3 -m pytest -q tests/test_auto_review_watch.py -k claude_and_codex` | `pass` (`--watch --once --dry` detects `claude` and `codex` fixtures) |
| Live watch daemon | `systemctl --user status auto-review-relay-watch.service` | `pass` (`active (running)`) |
