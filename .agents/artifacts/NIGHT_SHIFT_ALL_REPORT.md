# Multi-product night shift — 2026-07-28 19:15 UTC · 2026-07-29 03:15 HKT

**Overall:** FAIL (4/8 products)
**Schedule:** 03:15 Asia/Hong_Kong (harness timer)
**SoT:** `/home/debian/agent-harness`

| Product | Result | Exit | Root |
|---------|--------|------|------|
| watchlist | ❌ | 1 | `/home/debian/watchlist` |
| email-detach | ❌ | 1 | `/home/debian/email-detach` |
| substack-push | ✅ | 0 | `/home/debian/substack-push` |
| second-brain | ❌ | 1 | `/home/debian/second-brain` |
| catalyxt | ✅ | 0 | `/home/debian/catalyxt.ltd` |
| agent-harness | ✅ | 0 | `/home/debian/agent-harness` |
| ocr-ledger | ✅ | 0 | `/home/debian/ocr-ledger` |
| zk-business-card | ❌ | 1 | `/home/debian/zk-business-card` |

## Per-product failures (tails)

### watchlist
```
artifact: /home/debian/watchlist/.agents/artifacts/NIGHT_SHIFT_REPORT.md
artifact: /home/debian/watchlist/.agents/artifacts/NIGHT_SHIFT_TODO.md
vault log: /opt/second-brain/vault/01-Projects/watchlist/night-shift-log.md
vault TODO: /opt/second-brain/vault/01-Projects/watchlist/TODO.md
kanban: skip (not PASS)
⏭️  vault note skipped (dedupe or exists): /opt/second-brain/vault/01-Projects/watchlist/dev-log.md
❌ night_shift readiness watchlist FAIL (8/11)

```

### email-detach
```
artifact: /home/debian/email-detach/.agents/artifacts/NIGHT_SHIFT_REPORT.md
artifact: /home/debian/email-detach/.agents/artifacts/NIGHT_SHIFT_TODO.md
vault log: /opt/second-brain/vault/01-Projects/email-detach/night-shift-log.md
vault TODO: /opt/second-brain/vault/01-Projects/email-detach/TODO.md
kanban: skip (not PASS)
⏭️  vault note skipped (dedupe or exists): /opt/second-brain/vault/01-Projects/email-detach/dev-log.md
❌ night_shift readiness email-detach FAIL (5/6)

```

### second-brain
```
artifact: /home/debian/second-brain/.agents/artifacts/NIGHT_SHIFT_REPORT.md
artifact: /home/debian/second-brain/.agents/artifacts/NIGHT_SHIFT_TODO.md
vault log: /opt/second-brain/vault/01-Projects/second-brain/night-shift-log.md
vault TODO: /opt/second-brain/vault/01-Projects/second-brain/TODO.md
kanban: skip (not PASS)
⏭️  vault note skipped (dedupe or exists): /opt/second-brain/vault/01-Projects/second-brain/dev-log.md
❌ night_shift readiness second-brain FAIL (5/6)

```

### zk-business-card
```
artifact: /home/debian/zk-business-card/.agents/artifacts/NIGHT_SHIFT_REPORT.md
artifact: /home/debian/zk-business-card/.agents/artifacts/NIGHT_SHIFT_TODO.md
vault log: /opt/second-brain/vault/01-Projects/zk-business-card/night-shift-log.md
vault TODO: /opt/second-brain/vault/01-Projects/zk-business-card/TODO.md
kanban: skip (not PASS)
⏭️  vault note skipped (dedupe or exists): /opt/second-brain/vault/01-Projects/zk-business-card/dev-log.md
❌ night_shift readiness zk-business-card FAIL (7/8)

```


## Recommendations

1. Open each product vault `01-Projects/<label>/TODO.md` for checkboxes.
2. Fix failed products before `/execute_dev` on that repo.
3. **Hard-stop:** no multi-repo auto-release from this job.
