# Multi-product night-shift log

Newest-first multi-product runs (harness SoT). Times: **UTC · HKT**.

# Multi-product night shift — 2026-10-09 12:28 UTC · 2026-10-09 20:28 HKT

**Overall:** FAIL (0/11 products)
**Schedule:** 03:15 Asia/Hong_Kong (harness timer)
**SoT:** `~/agent-harness`

| Product | Result | Exit | Root |
|---------|--------|------|------|
| watchlist | ❌ | 1 | `~/watchlist` |
| email-detach | ❌ | 1 | `~/email-detach` |
| substack-push | ❌ | 1 | `~/substack-push` |
| second-brain | ❌ | 1 | `~/second-brain` |
| catalyxt | ❌ | 1 | `~/catalyxt-website` |
| agent-harness | ❌ | 1 | `~/agent-harness` |
| zk-business-card | ❌ | 1 | `~/zk-business-card` |
| bip39lab | ❌ | 1 | `~/bip39lab` |
| figure-it-out | ❌ | 1 | `~/figure-it-out` |
| jasmine | ❌ | 1 | `~/jasmine` |
| ui | ❌ | 1 | `~/catalyxt-ds` |

## Runtime (interpreter · port)

| Product | Python | Source | Port | Locked ports | Lock wait s |
|---------|--------|--------|------|--------------|-------------|
| watchlist | `~/watchlist/.venv/bin/python` | product-venv | 8765 | 8765 | 0.0 |
| email-detach | `~/email-detach/.venv/bin/python` | product-venv | - | - | 0.0 |
| substack-push | `~/substack-push/.venv/bin/python` | product-venv | - | - | 0.0 |
| second-brain | `~/second-brain/.venv/bin/python` | product-venv | - | - | 0.0 |
| catalyxt | `~/catalyxt-website/.venv/bin/python` | product-venv | 4178 | 4173,4178 | 0.0 |
| agent-harness | `~/agent-harness/.venv/bin/python` | product-venv | - | - | 0.0 |
| zk-business-card | `~/zk-business-card/.venv/bin/python` | product-venv | 5175 | 5175,8788 | 0.0 |
| bip39lab | `~/bip39lab/.venv/bin/python` | product-venv | 4173 | 4173 | 441.8 |
| figure-it-out | `~/figure-it-out/.venv/bin/python` | product-venv | 4176 | 4176 | 0.0 |
| jasmine | `~/agent-harness/.venv/bin/python` | harness-fallback (explicit python=harness; product has no venv) | 18273 | 18273 | 0.0 |
| ui | `~/agent-harness/.venv/bin/python` | harness-fallback (explicit python=harness; product has no venv) | 4177 | 4177 | 0.0 |

## vault_schema_lint drift vs harness SoT (report-only)

_All copies byte-identical._

## Per-product failures (tails)

### watchlist
```
artifact: ~/watchlist/.agents/artifacts/NIGHT_SHIFT_REPORT.md
artifact: ~/watchlist/.agents/artifacts/NIGHT_SHIFT_TODO.md
vault log: ~/agent-harness/01-Projects/watchlist/night-shift-log.md
vault TODO: ~/agent-harness/01-Projects/watchlist/TODO.md
✅ vault note prepended (newest-first): ~/agent-harness/01-Projects/watchlist/dev-log.md
❌ night_shift readiness watchlist FAIL (9/11)
night_shift_readiness: product=watchlist root=~/watchlist python=~/watchlist/.venv/bin/python

```

### email-detach
```
artifact: ~/email-detach/.agents/artifacts/NIGHT_SHIFT_REPORT.md
artifact: ~/email-detach/.agents/artifacts/NIGHT_SHIFT_TODO.md
vault log: ~/agent-harness/01-Projects/email-detach/night-shift-log.md
vault TODO: ~/agent-harness/01-Projects/email-detach/TODO.md
✅ vault note prepended (newest-first): ~/agent-harness/01-Projects/email-detach/dev-log.md
❌ night_shift readiness email-detach FAIL (5/6)
night_shift_readiness: product=email-detach root=~/email-detach python=~/email-detach/.venv/bin/python

```

### substack-push
```
artifact: ~/substack-push/.agents/artifacts/NIGHT_SHIFT_REPORT.md
artifact: ~/substack-push/.agents/artifacts/NIGHT_SHIFT_TODO.md
vault log: ~/agent-harness/01-Projects/substack-push/night-shift-log.md
vault TODO: ~/agent-harness/01-Projects/substack-push/TODO.md
✅ vault note prepended (newest-first): ~/agent-harness/01-Projects/substack-push/dev-log.md
❌ night_shift readiness substack-push FAIL (4/6)
night_shift_readiness: product=substack-push root=~/substack-push python=~/substack-push/.venv/bin/python

```

### second-brain
```
artifact: ~/second-brain/.agents/artifacts/NIGHT_SHIFT_REPORT.md
artifact: ~/second-brain/.agents/artifacts/NIGHT_SHIFT_TODO.md
vault log: ~/agent-harness/01-Projects/second-brain/night-shift-log.md
vault TODO: ~/agent-harness/01-Projects/second-brain/TODO.md
✅ vault note prepended (newest-first): ~/agent-harness/01-Projects/second-brain/dev-log.md
❌ night_shift readiness second-brain FAIL (5/6)
night_shift_readiness: product=second-brain root=~/second-brain python=~/second-brain/.venv/bin/python

```

### catalyxt
```
artifact: ~/catalyxt-website/.agents/artifacts/NIGHT_SHIFT_REPORT.md
artifact: ~/catalyxt-website/.agents/artifacts/NIGHT_SHIFT_TODO.md
vault log: ~/agent-harness/01-Projects/catalyxt/night-shift-log.md
vault TODO: ~/agent-harness/01-Projects/catalyxt/TODO.md
✅ vault note prepended (newest-first): ~/agent-harness/01-Projects/catalyxt/dev-log.md
❌ night_shift readiness catalyxt FAIL (5/6)
night_shift_readiness: product=catalyxt root=~/catalyxt-website python=~/catalyxt-website/.venv/bin/python

```

### agent-harness
```
artifact: ~/agent-harness/.agents/artifacts/NIGHT_SHIFT_REPORT.md
artifact: ~/agent-harness/.agents/artifacts/NIGHT_SHIFT_TODO.md
vault log: ~/agent-harness/01-Projects/agent-harness/night-shift-log.md
vault TODO: ~/agent-harness/01-Projects/agent-harness/TODO.md
✅ vault note prepended (newest-first): ~/agent-harness/01-Projects/agent-harness/dev-log.md
❌ night_shift readiness agent-harness FAIL (3/6)
night_shift_readiness: product=agent-harness root=~/agent-harness python=~/agent-harness/.venv/bin/python

```

### zk-business-card
```
artifact: ~/zk-business-card/.agents/artifacts/NIGHT_SHIFT_REPORT.md
artifact: ~/zk-business-card/.agents/artifacts/NIGHT_SHIFT_TODO.md
vault log: ~/agent-harness/01-Projects/zk-business-card/night-shift-log.md
vault TODO: ~/agent-harness/01-Projects/zk-business-card/TODO.md
✅ vault note prepended (newest-first): ~/agent-harness/01-Projects/zk-business-card/dev-log.md
❌ night_shift readiness zk-business-card FAIL (7/8)
night_shift_readiness: product=zk-business-card root=~/zk-business-card python=~/zk-business-card/.venv/bin/python

```

### bip39lab
```
artifact: ~/bip39lab/.agents/artifacts/NIGHT_SHIFT_REPORT.md
artifact: ~/bip39lab/.agents/artifacts/NIGHT_SHIFT_TODO.md
vault log: ~/agent-harness/01-Projects/bip39lab/night-shift-log.md
vault TODO: ~/agent-harness/01-Projects/bip39lab/TODO.md
✅ vault note prepended (newest-first): ~/agent-harness/01-Projects/bip39lab/dev-log.md
❌ night_shift readiness bip39lab FAIL (5/6)
night_shift_readiness: product=bip39lab root=~/bip39lab python=~/bip39lab/.venv/bin/python

```

### figure-it-out
```
artifact: ~/figure-it-out/.agents/artifacts/NIGHT_SHIFT_REPORT.md
artifact: ~/figure-it-out/.agents/artifacts/NIGHT_SHIFT_TODO.md
vault log: ~/agent-harness/01-Projects/figure-it-out/night-shift-log.md
vault TODO: ~/agent-harness/01-Projects/figure-it-out/TODO.md
✅ vault note prepended (newest-first): ~/agent-harness/01-Projects/figure-it-out/dev-log.md
❌ night_shift readiness figure-it-out FAIL (7/8)
night_shift_readiness: product=figure-it-out root=~/figure-it-out python=~/figure-it-out/.venv/bin/python

```

### jasmine
```
artifact: ~/jasmine/.agents/artifacts/NIGHT_SHIFT_REPORT.md
artifact: ~/jasmine/.agents/artifacts/NIGHT_SHIFT_TODO.md
vault log: ~/agent-harness/01-Projects/jasmine/night-shift-log.md
vault TODO: ~/agent-harness/01-Projects/jasmine/TODO.md
✅ vault note prepended (newest-first): ~/agent-harness/01-Projects/jasmine/dev-log.md
❌ night_shift readiness jasmine FAIL (5/6)
night_shift_readiness: product=jasmine root=~/jasmine python=~/agent-harness/.venv/bin/python

```

### ui
```
artifact: ~/catalyxt-ds/.agents/artifacts/NIGHT_SHIFT_REPORT.md
artifact: ~/catalyxt-ds/.agents/artifacts/NIGHT_SHIFT_TODO.md
vault log: ~/agent-harness/01-Projects/catalyxt-ds/night-shift-log.md
vault TODO: ~/agent-harness/01-Projects/catalyxt-ds/TODO.md
✅ vault note prepended (newest-first): ~/agent-harness/01-Projects/catalyxt-ds/dev-log.md
❌ night_shift readiness catalyxt-ds FAIL (8/9)
night_shift_readiness: product=catalyxt-ds root=~/catalyxt-ds python=~/agent-harness/.venv/bin/python

```


## Recommendations

1. Open each product vault `01-Projects/<label>/TODO.md` for checkboxes.
2. Fix failed products before `/execute_dev` on that repo.
3. **Hard-stop:** no multi-repo auto-release from this job.

---

