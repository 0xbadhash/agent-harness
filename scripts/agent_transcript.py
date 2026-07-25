#!/usr/bin/env python3
"""Best-effort local session find + sanitized markdown render (P3)."""
from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

_SECRETISH = re.compile(
    r"(-----BEGIN [A-Z ]*PRIVATE KEY-----|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{36,}"
    r"|xox[baprs]-[A-Za-z0-9-]{10,}|api[_-]?key\s*[:=]\s*['\"][^'\"]{16,})",
    re.I,
)
_DROP_LINE = re.compile(
    r"(system prompt|developer message|tool_result|authorization:\s*bearer|"
    r"cookie:|set-cookie:|/home/[a-z0-9]+/\.ssh)",
    re.I,
)


def _iter_candidate_logs(cwd: Path, since_days: int) -> list[Path]:
    roots = [
        cwd / ".agents" / "traces",
        Path.home() / ".grok" / "logs",
        Path.home() / ".grok" / "sessions",
        Path.home() / ".claude" / "projects",
    ]
    cutoff = datetime.now(timezone.utc) - timedelta(days=since_days)
    found: list[Path] = []
    for root in roots:
        if not root.is_dir():
            continue
        for p in root.rglob("*"):
            if not p.is_file():
                continue
            if p.suffix.lower() not in {".jsonl", ".json", ".log", ".txt", ".md"}:
                continue
            try:
                mtime = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc)
            except OSError:
                continue
            if mtime >= cutoff:
                found.append(p)
    found.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return found[:50]


def cmd_find(args: argparse.Namespace) -> int:
    cwd = Path(args.cwd).resolve()
    q = (args.query or "").lower().split()
    hits = _iter_candidate_logs(cwd, args.since_days)
    scored: list[tuple[int, Path]] = []
    for p in hits:
        score = 0
        s = str(p).lower()
        for tok in q:
            if tok and tok in s:
                score += 2
        try:
            sample = p.read_text(encoding="utf-8", errors="replace")[:8000].lower()
        except OSError:
            sample = ""
        for tok in q:
            if tok and tok in sample:
                score += 1
        scored.append((score, p))
    scored.sort(key=lambda x: (-x[0], -x[1].stat().st_mtime))
    if not scored:
        print("No local session candidates found")
        return 0
    print("file\tscore\tmtime")
    for score, p in scored[:15]:
        print(f"{p}\t{score}\t{datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc).isoformat()}")
    return 0


def sanitize(text: str) -> tuple[str, bool]:
    """Return (markdown, ok). ok False if unresolved secret patterns remain."""
    if _SECRETISH.search(text):
        # redacted attempt
        text = _SECRETISH.sub("[REDACTED]", text)
    if _SECRETISH.search(text):
        return "", False
    lines_out: list[str] = []
    for line in text.splitlines():
        if _DROP_LINE.search(line):
            continue
        if len(line) > 500:
            line = line[:500] + "…"
        lines_out.append(line)
    # cap size
    body = "\n".join(lines_out)
    if len(body) > 12000:
        body = body[:12000] + "\n…[truncated]"
    return body, True


def cmd_render(args: argparse.Namespace) -> int:
    path = Path(args.session)
    if not path.is_file():
        print(f"❌ not found: {path}", file=sys.stderr)
        return 1
    raw = path.read_text(encoding="utf-8", errors="replace")
    body, ok = sanitize(raw)
    if not ok:
        print("❌ fail closed: secret-like content could not be fully redacted", file=sys.stderr)
        return 1
    md = (
        "## Agent Transcript\n\n"
        "<details>\n<summary>Sanitized local session (best-effort)</summary>\n\n"
        f"Source: `{path.name}`\n\n```\n{body}\n```\n\n</details>\n"
    )
    out = Path(args.out) if args.out else None
    if out:
        out.write_text(md, encoding="utf-8")
        print(f"✅ wrote {out}")
    else:
        print(md)
    print("Ask the user before inserting into a PR/issue body.", file=sys.stderr)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("find")
    f.add_argument("--query", default="")
    f.add_argument("--cwd", default=".")
    f.add_argument("--since-days", type=int, default=14)
    f.set_defaults(func=cmd_find)
    r = sub.add_parser("render")
    r.add_argument("--session", required=True)
    r.add_argument("--out", default="")
    r.set_defaults(func=cmd_render)
    args = ap.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
