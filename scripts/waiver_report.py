#!/usr/bin/env python3
"""Summarize `.agents/artifacts/WAIVER_LOG.jsonl` (HSQ-1 AC-2).

  python3 scripts/waiver_report.py
  python3 scripts/waiver_report.py --root . --days 30
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path


def cluster_waivers(rows: list[dict]) -> dict[tuple[str, str], list[dict]]:
    """Group repeated waivers by gate and waiver type (E21 root-cause clusters).

    One waiver is an exception. Five waivers of the same type at the same gate
    are a broken gate or an unstated convention; that is the cluster to fix.
    """
    clusters: dict[tuple[str, str], list[dict]] = {}
    for row in rows:
        gate = str(row.get("gate") or "unknown")
        kind = str(row.get("waiver_type") or "?")
        clusters.setdefault((gate, kind), []).append(row)
    return clusters


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
    cutoff = datetime.now(UTC) - timedelta(days=max(1, args.days))
    by_type: Counter[str] = Counter()
    by_product: Counter[str] = Counter()
    rows: list[dict] = []
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
            when = when.replace(tzinfo=UTC)
        if when < cutoff:
            continue
        n += 1
        rows.append(row)
        by_type[str(row.get("waiver_type") or "?")] += 1
        by_product[str(row.get("product_id") or "?")] += 1
    print(f"waiver_report days={args.days} count={n} log={log}")
    if n:
        print("by_type:", dict(by_type))
        print("by_product:", dict(by_product))
        clusters = cluster_waivers(rows)
        print("clusters (gate · waiver_type · count):")
        for (gate, kind), members in sorted(
            clusters.items(), key=lambda item: (-len(item[1]), item[0])
        ):
            products = sorted({str(r.get("product_id") or "?") for r in members})
            print(f"  {gate} · {kind} · {len(members)} — products={products}")
            if len(members) >= 3:
                print(
                    f"    ⚠️  repeated waiver cluster at {gate}: fix the gate or the "
                    "convention instead of waiving again"
                )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
