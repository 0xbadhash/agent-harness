#!/usr/bin/env python3
"""G10 — bound Spec waiver use over a rolling window (default 30d, max 8)."""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

WAIVER_RE = re.compile(r"\*\*Spec waiver:\*\*\s*(hotfix|chore|docs-only|prose-only)\b", re.I)
DEFAULT_MAX = 8
DEFAULT_DAYS = 30


def check(
    root: Path,
    pr_draft: Path | None = None,
    *,
    max_waivers: int = DEFAULT_MAX,
    days: int = DEFAULT_DAYS,
) -> tuple[bool, list[str]]:
    root = root.resolve()
    log = root / ".agents" / "artifacts" / "WAIVER_LOG.jsonl"
    if not log.is_file():
        return True, ["ok: no WAIVER_LOG yet"]

    # Only enforce when *this* PR is itself a waiver (avoid punishing feature ships)
    if pr_draft and pr_draft.is_file():
        text = pr_draft.read_text(encoding="utf-8", errors="replace")
        if not WAIVER_RE.search(text):
            return True, ["ok: feature Spec (not a waiver ship)"]

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    count = 0
    for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        ts = str(row.get("ts") or "")
        try:
            when = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except ValueError:
            continue
        if when.tzinfo is None:
            when = when.replace(tzinfo=timezone.utc)
        if when >= cutoff:
            wtype = str(row.get("waiver_type") or "")
            if wtype in {"hotfix", "chore", "docs-only", "prose-only"}:
                count += 1
    if count > max_waivers:
        return False, [
            f"waiver budget exceeded: {count} in last {days}d (max {max_waivers}) — "
            "use a real Spec for feature work"
        ]
    return True, [f"ok: waiver count {count}/{max_waivers} in {days}d"]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--pr-draft", type=Path, default=None)
    ap.add_argument("--max", type=int, default=DEFAULT_MAX)
    ap.add_argument("--days", type=int, default=DEFAULT_DAYS)
    args = ap.parse_args(argv)
    root = args.root.resolve()
    draft = args.pr_draft or (root / "PR_DRAFT.md")
    ok, msgs = check(root, draft, max_waivers=args.max, days=args.days)
    for m in msgs:
        print(("✅ " if ok else "❌ ") + m)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
