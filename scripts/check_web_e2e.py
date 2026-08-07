#!/usr/bin/env python3
"""Gate: when product has a website, require Playwright + Comet scenario contract."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from web_e2e_contract import validate_web_e2e  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--json", action="store_true")
    ap.add_argument(
        "--strict-surfaces",
        action="store_true",
        help="Fail if website detected but web_e2e.surfaces missing",
    )
    args = ap.parse_args()
    root = args.root.resolve()
    r = validate_web_e2e(root)
    if args.strict_surfaces and r.get("has_website"):
        warns = r.get("warnings") or []
        if any("surfaces not declared" in w for w in warns):
            r["pass"] = False
            r.setdefault("violations", []).append(
                "strict: declare web_e2e.surfaces for deterministic S0..Sn"
            )

    if args.json:
        print(json.dumps(r, indent=2))
    else:
        if not r.get("has_website"):
            print("⏭️  no website detected — web_e2e skipped")
            return 0
        print(f"website: yes ({', '.join(r.get('reasons') or [])})")
        for v in r.get("violations") or []:
            print(f"❌ {v}")
        for w in r.get("warnings") or []:
            print(f"⚠️  {w}")
        sc = r.get("scenarios") or []
        if sc:
            print("IDs:", " ".join(x["global_id"] for x in sc))
        print("✅ check_web_e2e ok" if r.get("pass") else "❌ check_web_e2e failed")
    return 0 if r.get("pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
