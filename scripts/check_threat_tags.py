#!/usr/bin/env python3
"""G7 — runtime threat notes must include ≥2 known security tags."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

TAGS = (
    "authz",
    "authn",
    "secrets",
    "injection",
    "ssrf",
    "path-traversal",
    "path_traversal",
    "xss",
    "csrf",
    "multi-tenant",
    "tenancy",
    "supply-chain",
    "rce",
    "idor",
)
THREAT_RE = re.compile(r"##\s+Threat notes\b(.*?)(?=\n## |\Z)", re.I | re.S)


def check(draft_text: str, *, runtime: bool) -> tuple[bool, list[str]]:
    if not runtime:
        return True, ["ok: not runtime — threat tags N/A"]
    m = THREAT_RE.search(draft_text)
    if not m:
        return False, ["## Threat notes missing for runtime ship"]
    body = m.group(1).lower()
    hit = [t for t in TAGS if t in body]
    # normalize path_traversal/path-traversal
    uniq = set(h.replace("_", "-") for h in hit)
    if len(uniq) < 2:
        return False, [
            "Threat notes need ≥2 tags from: "
            + ", ".join(sorted(set(t.replace("_", "-") for t in TAGS)))
            + f" (found: {sorted(uniq) or 'none'})"
        ]
    return True, [f"ok: threat tags {sorted(uniq)}"]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pr-draft", type=Path, required=True)
    ap.add_argument("--runtime", action="store_true")
    args = ap.parse_args(argv)
    text = args.pr_draft.read_text(encoding="utf-8", errors="replace")
    ok, msgs = check(text, runtime=args.runtime)
    for m in msgs:
        print(("✅ " if ok else "❌ ") + m)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
