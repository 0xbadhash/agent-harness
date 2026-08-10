#!/usr/bin/env python3
"""Summarize `.agents/artifacts/WAIVER_LOG.jsonl` (HSQ-1 AC-2).

  python3 scripts/waiver_report.py
  python3 scripts/waiver_report.py --root . --days 30
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--days", type=int, default=30)
    args = ap.parse_args(argv)
    root = args.root.resolve()
    log = root / ".agents" / "artifacts" / "WAIVER_LOG.jsonl"
    if not log.is_file():
        print(f"no waiver log at {log}")
        return 0
    cutoff = datetime.now(timezone.utc) - timedelta(days=max(1, args.days))
    by_type: Counter[str] = Counter()
    by_product: Counter[str] = Counter()
    n = 0
    for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        ts = row.get("ts") or ""
        try:
            when = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except ValueError:
            when = cutoff  # include unparseable in window
        if when.tzinfo is None:
            when = when.replace(tzinfo=timezone.utc)
        if when < cutoff:
            continue
        n += 1
        by_type[str(row.get("waiver_type") or "?")] += 1
        by_product[str(row.get("product_id") or "?")] += 1
    print(f"waiver_report days={args.days} count={n} log={log}")
    if n:
        print("by_type:", dict(by_type))
        print("by_product:", dict(by_product))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
