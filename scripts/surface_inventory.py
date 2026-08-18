#!/usr/bin/env python3
"""Declared Catalyxt surface inventory (portable; no domain-find).

Default invocation (pane / operator)::

  python3 scripts/surface_inventory.py

Always lists **known** hosts shipped with this harness (and any extra from
``config/zap_targets.yaml``). Does **not** scan DNS/CT/internet for new names.
Does **not** invent typo domains. Optional ``--probe`` may HEAD/GET declared
URLs only. Optional ``--write`` writes
``.agents/artifacts/SURFACE_INVENTORY.md``.

Not a night/ship hard gate. Not added to ``night_shift_all``.
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

# Known Catalyxt hosts already in the portfolio surface (CEO list). No typos.
KNOWN_CATALYXT_HOSTS: tuple[tuple[str, str], ...] = (
    ("catalyxt", "https://catalyxt.xyz"),
    ("watchlist", "https://watchlist.catalyxt.xyz"),
    ("artauthenticity", "https://artauthenticity.xyz"),
    ("bip39lab", "https://bip39.catalyxt.xyz"),
    ("figure-it-out", "https://figure.catalyxt.xyz"),
    ("zk-business-card", "https://card.catalyxt.xyz"),
    ("ui", "https://ui.catalyxt.xyz"),
)


def _parse_zap_targets(cfg: Path) -> list[dict[str, str]]:
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


def _merge_targets(zap_cfg: Path) -> list[dict[str, str]]:
    """Known list first, then zap_targets extras (dedupe by URL host+path)."""
    seen: set[str] = set()
    out: list[dict[str, str]] = []
    for tid, url in KNOWN_CATALYXT_HOSTS:
        key = url.rstrip("/").lower()
        if key in seen:
            continue
        seen.add(key)
        out.append({"id": tid, "url": url, "source": "known"})
    for row in _parse_zap_targets(zap_cfg):
        url = (row.get("url") or "").rstrip("/")
        key = url.lower()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(
            {
                "id": row.get("id") or "zap",
                "url": url,
                "source": "zap_targets",
            }
        )
    return out


def _probe(url: str, timeout: float = 12.0) -> tuple[str, str]:
    req = urllib.request.Request(url, method="HEAD")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
            return str(getattr(resp, "status", 200)), "ok"
    except urllib.error.HTTPError as e:
        return str(e.code), "http_error"
    except Exception as e:  # noqa: BLE001
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
        help="Optional zap_targets.yaml to merge (extras only)",
    )
    ap.add_argument(
        "--probe",
        action="store_true",
        help="HEAD/GET each *declared* URL only (still no discovery)",
    )
    ap.add_argument(
        "--write",
        action="store_true",
        help="Write .agents/artifacts/SURFACE_INVENTORY.md",
    )
    ap.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 if --probe and any URL is not 2xx/3xx",
    )
    args = ap.parse_args(argv)
    root = args.root.resolve()

    cfg = args.config or Path(
        os.environ.get("ZAP_TARGETS_FILE") or (root / "config" / "zap_targets.yaml")
    )
    targets = _merge_targets(cfg)
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# SURFACE_INVENTORY",
        "",
        f"_Generated {now} by `scripts/surface_inventory.py`_",
        "",
        f"**Known hosts:** {len(KNOWN_CATALYXT_HOSTS)} (CEO list) · "
        f"**zap merge:** `{cfg.name if cfg.is_file() else 'n/a'}`",
        f"**Probe:** {'yes (declared URLs only)' if args.probe else 'no (list only)'}",
        "",
        "| id | url | status | source |",
        "|----|-----|--------|--------|",
    ]
    bad = 0
    for t in targets:
        url = t.get("url") or ""
        tid = t.get("id") or ""
        src = t.get("source") or ""
        if args.probe:
            status, note = _probe(url)
            src = f"{src}/{note}"
            if not re.match(r"^2\d\d$|^3\d\d$", status):
                bad += 1
        else:
            status = "—"
        lines.append(f"| {tid} | `{url}` | {status} | {src} |")
    if not targets:
        lines.append("| — | — | — | empty |")
    lines.extend(
        [
            "",
            "> Declared / known surfaces only — **no** DNS/CT/internet discovery.",
            "> Not a night/ship hard gate. ZAP remains schedule/manual, not night_all.",
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
    # Pane default call must succeed (exit 0) even without env flags
    if args.strict and args.probe and bad:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
