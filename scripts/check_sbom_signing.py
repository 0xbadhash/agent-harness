#!/usr/bin/env python3
"""Tier C-3: SBOM / signing readiness checklist (warn-only by default).

  python3 scripts/check_sbom_signing.py --root .
  python3 scripts/check_sbom_signing.py --root . --strict  # fail if nothing present
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

CANDIDATES = (
    "sbom.spdx.json",
    "sbom.cdx.json",
    "bom.json",
    ".github/workflows/sbom.yml",
    "cosign.pub",
    "docs/signing.md",
)


def check(root: Path, *, strict: bool) -> tuple[bool, list[str]]:
    root = root.resolve()
    found = [c for c in CANDIDATES if (root / c).exists()]
    msgs = [f"found: {', '.join(found)}" if found else "no SBOM/signing artifacts yet"]
    if found:
        msgs.append("ok: at least one SBOM/signing path present (scaffold)")
        return True, msgs
    if strict:
        return False, msgs + ["strict: add sbom or docs/signing.md"]
    msgs.append("warn: optional Tier C-3 — document when product ships signed releases")
    return True, msgs


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args(argv)
    ok, msgs = check(args.root.resolve(), strict=bool(args.strict))
    for m in msgs:
        pref = "✅ " if m.startswith("ok:") else ("❌ " if not ok else "⚠️  ")
        print(pref + m)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
