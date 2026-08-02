# MORNING_TRIAGE

_Generated 2026-08-02 09:31 UTC by night_shift_morning_triage.py_

**Overall:** FAIL

| Product | Path | Night overall | Fail gates | Recheck | Notes |
|---------|------|---------------|------------|---------|-------|
| `watchlist` | `/home/debian/watchlist` | **FAIL** | validate_full, product_smoke | no | — |
| `email-detach` | `/home/debian/email-detach` | **PASS** | — | no | — |
| `substack-push` | `/home/debian/substack-push` | **FAIL** | hardcodes, validate_full, product_smoke | no | — |
| `second-brain` | `/home/debian/second-brain` | **PASS** | — | no | — |
| `catalyxt` | `/home/debian/catalyxt.ltd` | **PASS** | — | no | — |
| `agent-harness` | `/home/debian/agent-harness` | **PASS** | — | no | — |
| `ocr-ledger` | `/home/debian/ocr-ledger` | **PASS** | — | no | — |
| `zk-business-card` | `/home/debian/zk-business-card` | **PASS** | — | no | — |

## Operator next

- If **PASS**: safe to start product work.
- If **FAIL**: open product `.agents/artifacts/NIGHT_SHIFT_TODO.md` or vault TODO; fix gates then re-run readiness.
- This tool does **not** auto-ship. Unattended `/execute_dev` is out of scope.

