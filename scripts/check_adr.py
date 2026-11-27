#!/usr/bin/env python3
"""Validate the architecture decision record spine.

Checks ``.agents/decisions/``:

- ``README.md`` indexes every ADR file and every link resolves.
- Each ``NNN-<slug>.md`` has a matching ``# ADR NNN`` header and a status.
- Each ADR states reversibility, surprise, and tradeoff (the E13 contract).
- ``--strict`` also fails an empty spine.

Usage::

  python3 scripts/check_adr.py --root .
  python3 scripts/check_adr.py --root . --strict
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ADR_NAME_RE = re.compile(r"^(\d{3})-[a-z0-9-]+\.md$")
HEADER_RE = re.compile(r"^#\s+ADR\s+(\d{3})\b", re.MULTILINE)
STATUS_RE = re.compile(
    r"^\*\*Status:\*\*\s*(proposed|accepted|superseded|rejected)\b",
    re.IGNORECASE | re.MULTILINE,
)
LINK_RE = re.compile(r"\]\(([^)\s]+\.md)\)")
REVERSIBLE_RE = re.compile(r"reversib", re.IGNORECASE)
SURPRISE_RE = re.compile(r"surpris", re.IGNORECASE)
TRADEOFF_RE = re.compile(r"trade[-\s]?off", re.IGNORECASE)
SKIP = {"README.md", "000-template.md"}


def check(root: Path, *, strict: bool = False) -> tuple[bool, list[str]]:
    """Return (ok, messages) for the decisions directory."""
    root = Path(root)
    decisions = root / ".agents" / "decisions"
    msgs: list[str] = []
    if not decisions.is_dir():
        return False, [f"missing decisions directory: {decisions.relative_to(root)}"]

    index = decisions / "README.md"
    if not index.is_file():
        return False, ["missing .agents/decisions/README.md index"]
    index_text = index.read_text(encoding="utf-8", errors="replace")

    adrs = sorted(p for p in decisions.glob("*.md") if p.name not in SKIP)
    if not adrs:
        if strict:
            return False, ["no ADRs recorded (strict)"]
        return True, ["ok: decisions spine present, no ADRs yet"]

    failures: list[str] = []
    for path in adrs:
        name_match = ADR_NAME_RE.match(path.name)
        body = path.read_text(encoding="utf-8", errors="replace")
        if name_match is None:
            failures.append(f"{path.name}: name must be NNN-<slug>.md")
            continue
        number = name_match.group(1)
        header = HEADER_RE.search(body)
        if header is None:
            failures.append(f"{path.name}: missing '# ADR {number}' header")
        elif header.group(1) != number:
            failures.append(
                f"{path.name}: header says ADR {header.group(1)}, filename says {number}"
            )
        if STATUS_RE.search(body) is None:
            failures.append(f"{path.name}: missing **Status:** line")
        missing = [
            label
            for label, rx in (
                ("reversibility", REVERSIBLE_RE),
                ("surprise", SURPRISE_RE),
                ("tradeoff", TRADEOFF_RE),
            )
            if rx.search(body) is None
        ]
        if missing:
            failures.append(
                f"{path.name}: missing {'/'.join(missing)} — state all three parts"
            )
        if path.name not in index_text:
            failures.append(f"{path.name}: not listed in README.md")

    for target in LINK_RE.findall(index_text):
        if target.startswith(("http://", "https://")):
            continue
        if not (decisions / target).is_file():
            failures.append(f"README.md: link {target!r} does not resolve")

    if failures:
        return False, failures
    return True, [f"ok: {len(adrs)} ADR(s) indexed and complete"]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args(argv)
    ok, msgs = check(args.root, strict=args.strict)
    for msg in msgs:
        print(("✅ " if ok else "❌ ") + msg)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
