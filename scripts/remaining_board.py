#!/usr/bin/env python3
"""A2/B6 — durable REMAINING.md board (roadmap OPEN + night fails + phase).

  python3 scripts/remaining_board.py
  python3 scripts/remaining_board.py --root /path/to/product

Call after ship / morning triage so sessions do not re-ask “what remaining?”.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

OPEN_RE = re.compile(
    r"^### \[OPEN\][^\n]*\n(.*?)(?=^### |\Z)",
    re.M | re.S,
)


def _rel(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def _phase(root: Path) -> str:
    p = root / ".agents" / "state" / "pipeline.json"
    if not p.is_file():
        return "unknown"
    try:
        return str(json.loads(p.read_text(encoding="utf-8")).get("phase") or "unknown")
    except json.JSONDecodeError:
        return "unknown"


def _open_items(roadmap: Path) -> list[str]:
    if not roadmap.is_file():
        return []
    text = roadmap.read_text(encoding="utf-8", errors="replace")
    items: list[str] = []
    for m in re.finditer(r"^### \[OPEN\]\s*(.+)$", text, re.M):
        items.append(m.group(1).strip())
    return items


def _night_summary(root: Path) -> list[str]:
    lines: list[str] = []
    for name in ("MORNING_TRIAGE.md", "NIGHT_FAIL_PROMOTIONS.md", "NIGHT_SHIFT_TODO.md"):
        p = root / ".agents" / "artifacts" / name
        if not p.is_file():
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        if "FAIL" in text or "PROMOTION" in text or "Lagging" in text:
            # first non-empty content line with FAIL or header
            for ln in text.splitlines()[:15]:
                if "FAIL" in ln or "Lagging" in ln or "Gate" in ln:
                    lines.append(f"{name}: {ln.strip()[:120]}")
                    break
            else:
                lines.append(f"{name}: present")
    return lines


def write_board(root: Path, out: Path | None = None) -> Path:
    root = root.resolve()
    out = out or (root / ".agents" / "artifacts" / "REMAINING.md")
    out.parent.mkdir(parents=True, exist_ok=True)

    # roadmap path from plugin or CHANGELOG
    roadmap = root / "CHANGELOG.md"
    plugin = root / ".agents" / "product_plugin.yaml"
    if plugin.is_file():
        for ln in plugin.read_text(encoding="utf-8", errors="replace").splitlines():
            if ln.strip().startswith("product_roadmap:"):
                rel = ln.split(":", 1)[1].strip()
                cand = root / rel
                if cand.is_file():
                    roadmap = cand
                break

    phase = _phase(root)
    opens = _open_items(roadmap)
    night = _night_summary(root)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        "# REMAINING",
        "",
        f"_Updated {now} by remaining_board.py_",
        "",
        f"**Pipeline phase:** `{phase}`",
        f"**Roadmap file:** `{_rel(root, roadmap)}`",
        "",
        "## Open roadmap items",
        "",
    ]
    if opens:
        for o in opens:
            lines.append(f"- [ ] {o}")
    else:
        lines.append("- (none marked `[OPEN]`)")
    lines.extend(["", "## Night / portfolio signals", ""])
    if night:
        for n in night:
            lines.append(f"- {n}")
    else:
        lines.append("- (no MORNING_TRIAGE / NIGHT_FAIL_PROMOTIONS / TODO signals)")
    lines.extend(
        [
            "",
            "## Refresh",
            "",
            "```bash",
            "python3 scripts/remaining_board.py",
            "python3 scripts/night_shift_morning_triage.py",
            "python3 scripts/promote_night_fails.py",
            "python3 scripts/portfolio_install_report.py",
            "python3 scripts/finish_ship.py --require-push",
            "```",
            "",
        ]
    )
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args(argv)
    path = write_board(args.root, args.out)
    print(f"remaining_board out={path}")
    print(path.read_text(encoding="utf-8")[:500])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
