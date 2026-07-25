#!/usr/bin/env python3
"""Minimal session JSONL/text → single-file HTML viewer (portable P3)."""
from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path


def load_events(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8", errors="replace")
    events: list[dict] = []
    # JSONL
    if path.suffix.lower() in {".jsonl", ".json"} or "\n{" in text[:2000]:
        for line in text.splitlines():
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        if events:
            return events
        try:
            data = json.loads(text)
            if isinstance(data, list):
                return [x for x in data if isinstance(x, dict)]
            if isinstance(data, dict):
                return [data]
        except json.JSONDecodeError:
            pass
    # Plain text fallback: wrap as user lines
    return [{"role": "log", "content": line} for line in text.splitlines() if line.strip()]


def extract_text(ev: dict) -> tuple[str, str]:
    role = str(ev.get("role") or ev.get("type") or ev.get("kind") or "event")
    for key in ("content", "text", "message", "body"):
        val = ev.get(key)
        if isinstance(val, str) and val.strip():
            return role, val
        if isinstance(val, list):
            parts = []
            for block in val:
                if isinstance(block, dict) and block.get("type") == "text":
                    parts.append(str(block.get("text") or ""))
                elif isinstance(block, str):
                    parts.append(block)
            if parts:
                return role, "\n".join(parts)
    # compact dump
    return role, json.dumps({k: ev[k] for k in list(ev)[:8]}, ensure_ascii=False)[:2000]


def render_html(events: list[dict], title: str) -> str:
    rows = []
    for ev in events[:2000]:
        role, body = extract_text(ev)
        rows.append(
            f'<div class="msg"><div class="role">{html.escape(role)}</div>'
            f'<pre>{html.escape(body[:8000])}</pre></div>'
        )
    body = "\n".join(rows) or "<p>No events parsed.</p>"
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"/>
<title>{html.escape(title)}</title>
<style>
body{{font-family:system-ui,sans-serif;margin:1rem 2rem;background:#0f1115;color:#e8eaed}}
.msg{{border:1px solid #333;border-radius:8px;margin:.6rem 0;padding:.6rem .8rem;background:#1a1d24}}
.role{{font-weight:600;color:#8ab4f8;margin-bottom:.4rem}}
pre{{white-space:pre-wrap;word-break:break-word;margin:0;font-size:13px}}
input{{width:100%;padding:.5rem;margin-bottom:1rem;background:#111;color:#eee;border:1px solid #444}}
</style></head><body>
<h1>{html.escape(title)}</h1>
<input id="q" placeholder="Filter…" oninput="filter()"/>
<div id="log">{body}</div>
<script>
function filter(){{
  const q=document.getElementById('q').value.toLowerCase();
  document.querySelectorAll('.msg').forEach(el=>{{
    el.style.display = !q || el.innerText.toLowerCase().includes(q) ? '' : 'none';
  }});
}}
</script></body></html>
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("session", type=Path, nargs="?", help="Path to .jsonl / .json / .txt")
    ap.add_argument("--out", type=Path, default=Path("/tmp/session.html"))
    ap.add_argument("--blank", action="store_true")
    args = ap.parse_args()
    if args.blank or not args.session:
        html_out = render_html([], "Session viewer")
    else:
        if not args.session.is_file():
            print(f"❌ not found: {args.session}", file=sys.stderr)
            return 1
        events = load_events(args.session)
        html_out = render_html(events, args.session.name)
    args.out.write_text(html_out, encoding="utf-8")
    print(f"✅ wrote {args.out} ({args.out.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
