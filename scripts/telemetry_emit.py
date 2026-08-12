#!/usr/bin/env python3
"""Tier C-5: optional local telemetry JSONL (opt-in via HARNESS_TELEMETRY=1).

  HARNESS_TELEMETRY=1 python3 scripts/telemetry_emit.py --event ship_closeout --kv phase=approved
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path


def emit(root: Path, event: str, kv: dict[str, str]) -> Path | None:
    if os.environ.get("HARNESS_TELEMETRY", "").strip() not in {"1", "true", "yes", "on"}:
        print("telemetry off (set HARNESS_TELEMETRY=1)", file=sys.stderr)
        return None
    path = root / ".agents" / "artifacts" / "telemetry.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "ts": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "event": event,
        **kv,
    }
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, sort_keys=True) + "\n")
    print(f"✅ telemetry → {path}")
    return path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--event", required=True)
    ap.add_argument("--kv", action="append", default=[], help="key=value")
    args = ap.parse_args(argv)
    kv: dict[str, str] = {}
    for item in args.kv:
        if "=" in item:
            k, v = item.split("=", 1)
            kv[k] = v
    emit(args.root.resolve(), args.event, kv)
    return 0


if __name__ == "__main__":
    sys.exit(main())
