#!/usr/bin/env python3
"""Optional declared-surface inventory (portable; default off).

Reads URLs from ``config/zap_targets.yaml`` (or ``--config`` / ``ZAP_TARGETS_FILE``).
Optionally probes live HTTP status. Writes an artifact — does **not** embed into
docs SoT, does **not** enumerate DNS/CT (no domain-find), does **not** add ZAP
to the night loop.

Enable::

  SURFACE_INVENTORY=1 python3 scripts/surface_inventory.py
  python3 scripts/surface_inventory.py --probe --write

Exit 0 always unless ``--strict`` and a probed URL is non-2xx/3xx.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

HARNESS = Path(__file__).resolve().parents[1]


def _enabled(cli_force: bool) -> bool:
    if cli_force:
        return True
    return os.environ.get("SURFACE_INVENTORY", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _parse_targets(cfg: Path) -> list[dict[str, str]]:
    if not cfg.is_file():
        return []
    rows: list[dict[str, str]] = []
    cur: dict[str, str] = {}
    enabled = True
    for line in cfg.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s.startswith("- id:"):
            if cur.get("url") and enabled:
                rows.append(dict(cur))
            cur = {"id": s.split(":", 1)[1].strip()}
            enabled = True
        elif s.startswith("enabled:"):
            enabled = s.split(":", 1)[1].strip().lower() in ("true", "yes", "1")
        elif s.startswith("url:"):
            cur["url"] = s.split(":", 1)[1].strip()
    if cur.get("url") and enabled:
        rows.append(dict(cur))
    return rows


def _probe(url: str, timeout: float = 12.0) -> tuple[str, str]:
    req = urllib.request.Request(url, method="HEAD")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
            return str(getattr(resp, "status", 200)), "ok"
    except urllib.error.HTTPError as e:
        return str(e.code), "http_error"
    except Exception as e:  # noqa: BLE001
        # Some hosts reject HEAD — try GET
        try:
            req2 = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req2, timeout=timeout) as resp:  # noqa: S310
                return str(getattr(resp, "status", 200)), "ok_get"
        except Exception as e2:  # noqa: BLE001
            return "000", f"{type(e).__name__}/{type(e2).__name__}"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=HARNESS)
    ap.add_argument(
        "--config",
        type=Path,
        default=None,
        help="zap_targets.yaml (default: <root>/config/zap_targets.yaml)",
    )
    ap.add_argument("--probe", action="store_true", help="HEAD/GET each declared URL")
    ap.add_argument("--write", action="store_true", help="Write artifact under .agents/artifacts/")
    ap.add_argument("--force", action="store_true", help="Run even if SURFACE_INVENTORY unset")
    ap.add_argument("--strict", action="store_true", help="Exit 1 if any probe fails")
    args = ap.parse_args(argv)
    root = args.root.resolve()

    if not _enabled(bool(args.force)):
        print(
            "surface_inventory off (set SURFACE_INVENTORY=1 or pass --force)",
            file=sys.stderr,
        )
        return 0

    cfg = args.config or Path(
        os.environ.get("ZAP_TARGETS_FILE") or (root / "config" / "zap_targets.yaml")
    )
    targets = _parse_targets(cfg)
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# SURFACE_INVENTORY",
        "",
        f"_Generated {now} by `scripts/surface_inventory.py`_",
        "",
        f"**Config:** `{cfg}`",
        f"**Probe:** {'yes' if args.probe else 'no (declared only)'}",
        "",
        "| id | url | status | note |",
        "|----|-----|--------|------|",
    ]
    bad = 0
    for t in targets:
        url = t.get("url") or ""
        tid = t.get("id") or ""
        status, note = ("—", "declared") if not args.probe else _probe(url)
        if args.probe and not re.match(r"^2\d\d$|^3\d\d$", status):
            bad += 1
        lines.append(f"| {tid} | `{url}` | {status} | {note} |")
    if not targets:
        lines.append("| — | — | — | no targets in config |")
    lines.extend(
        [
            "",
            "> Declared surfaces only — no DNS/CT crawl. Not a night/ship hard gate.",
            "",
        ]
    )
    md = "\n".join(lines)
    print(md)
    if args.write:
        out = root / ".agents" / "artifacts" / "SURFACE_INVENTORY.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(md, encoding="utf-8")
        print(f"✅ wrote {out}", file=sys.stderr)
    if args.strict and bad:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
