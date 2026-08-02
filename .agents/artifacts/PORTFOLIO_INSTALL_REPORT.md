# PORTFOLIO_INSTALL_REPORT

_Generated 2026-08-02 09:36 UTC · harness SoT VERSION=`1.4.11`_

**Lagging products:** 7 / 7

| Product | Path | HARNESS_VERSION | Lagging | Notes |
|---------|------|-----------------|---------|-------|
| `watchlist` | `/home/debian/watchlist` | `1.4.10` | YES | product '1.4.10' != SoT '1.4.11' |
| `email-detach` | `/home/debian/email-detach` | `﻿1.4.10` | YES | product '\ufeff1.4.10' != SoT '1.4.11' |
| `substack-push` | `/home/debian/substack-push` | `1.4.10` | YES | product '1.4.10' != SoT '1.4.11' |
| `second-brain` | `/home/debian/second-brain` | `1.4.10` | YES | product '1.4.10' != SoT '1.4.11' |
| `catalyxt` | `/home/debian/catalyxt.ltd` | `1.4.10` | YES | product '1.4.10' != SoT '1.4.11' |
| `ocr-ledger` | `/home/debian/ocr-ledger` | `1.4.10` | YES | product '1.4.10' != SoT '1.4.11' |
| `zk-business-card` | `/home/debian/zk-business-card` | `1.4.10` | YES | product '1.4.10' != SoT '1.4.11' |

## Commands

```bash
python3 scripts/portfolio_install_report.py
python3 scripts/portfolio_install_report.py --install
python3 scripts/portfolio_install_report.py --install --push
```

Default report-only. `--push` only after successful install commit.

