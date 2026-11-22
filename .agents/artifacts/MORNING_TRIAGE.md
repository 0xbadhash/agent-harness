# MORNING_TRIAGE

_Generated 2026-11-21 20:03 UTC by night_shift_morning_triage.py_

**Overall:** FAIL

| Product | Path | Night overall | Fail gates | Recheck | Notes |
|---------|------|---------------|------------|---------|-------|
| `watchlist` | `/home/debian/watchlist` | **FAIL** | validate_full, product_smoke | no | — |
| `email-detach` | `/home/debian/email-detach` | **PASS** | — | no | — |
| `substack-push` | `/home/debian/substack-push` | **PASS** | — | no | — |
| `second-brain` | `/home/debian/second-brain` | **PASS** | — | no | — |
| `catalyxt` | `/home/debian/catalyxt-website` | **PASS** | — | no | — |
| `agent-harness` | `/home/debian/agent-harness` | **PASS** | — | no | — |
| `zk-business-card` | `/home/debian/zk-business-card` | **FAIL** | live_http_0 | no | — |
| `bip39lab` | `/home/debian/bip39lab` | **PASS** | — | no | — |
| `figure-it-out` | `/home/debian/figure-it-out` | **FAIL** | product_smoke | no | — |
| `jasmine` | `/home/debian/jasmine` | **PASS** | — | no | — |
| `ui` | `/home/debian/catalyxt-ds` | **FAIL** | validate_full | no | — |
| `mission-feeds` | `/home/debian/.local/lib/mission-feeds` | **PASS** | — | no | — |

## Operator next

- If **PASS**: safe to start product work.
- If **FAIL**: open product `.agents/artifacts/NIGHT_SHIFT_TODO.md` or vault TODO; fix gates then re-run readiness.
- This tool does **not** auto-ship. Unattended `/execute_dev` is out of scope.

