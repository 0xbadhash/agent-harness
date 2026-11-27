#!/usr/bin/env python3
"""Correction -> check map: review findings must name the check that prevents them.

Reads ``.agents/artifacts/CODE_REVIEW.md`` and requires a
``## Correction checks`` section. Every bullet must map a finding to a
deterministic check (test, lint rule, gate, smoke) or to a signed
``no-check: <reason>``. A review with no accepted findings writes ``- none``.

Usage::

  python3 scripts/check_correction_checks.py --root .
  python3 scripts/check_correction_checks.py --root . --warn-only
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARTIFACT = Path(".agents") / "artifacts" / "CODE_REVIEW.md"
HEADER_RE = re.compile(r"^##\s+Correction checks\b", re.IGNORECASE | re.MULTILINE)
SECTION_RE = re.compile(
    r"^##\s+Correction checks\b(.*?)(?=^##\s|\Z)",
    re.IGNORECASE | re.MULTILINE | re.DOTALL,
)
BULLET_RE = re.compile(r"^\s*[-*]\s+(.+)$", re.MULTILINE)
ARROW_RE = re.compile(r"(?:→|->)")
NONE_RE = re.compile(r"^none\b", re.IGNORECASE)
NO_CHECK_RE = re.compile(r"^\s*no-check:\s*(.*)$", re.IGNORECASE)
CHECK_TOKEN_RE = re.compile(
    r"\b(tests?|pytest|lint|gate|ruff|rules?|checks?|guard|assert|hypothesis|smoke|ci)\b|"
    r"tests?/",
    re.IGNORECASE,
)
MIN_NO_CHECK_REASON = 10


def check(root: Path) -> tuple[bool, list[str]]:
    """Return (ok, messages) for the correction->check map."""
    path = Path(root) / ARTIFACT
    if not path.is_file():
        return True, ["correction_checks: no CODE_REVIEW.md (gated elsewhere)"]
    text = path.read_text(encoding="utf-8", errors="replace")
    if not HEADER_RE.search(text):
        return False, [
            "correction_checks: CODE_REVIEW.md missing '## Correction checks' — "
            "map each accepted finding to a check, or write '- none'"
        ]
    match = SECTION_RE.search(text)
    body = match.group(1) if match else ""
    bullets = [b.strip() for b in BULLET_RE.findall(body) if b.strip()]
    if not bullets:
        return False, [
            "correction_checks: '## Correction checks' is empty — "
            "add one bullet per accepted finding, or '- none'"
        ]
    if len(bullets) == 1 and NONE_RE.match(bullets[0]):
        return True, ["correction_checks: no accepted findings"]
    problems: list[str] = []
    for bullet in bullets:
        if NONE_RE.match(bullet) and not ARROW_RE.search(bullet):
            continue
        if not ARROW_RE.search(bullet):
            problems.append(f"unmapped finding: {bullet[:100]}")
            continue
        target = ARROW_RE.split(bullet, 1)[1].strip()
        no_check = NO_CHECK_RE.match(target)
        if no_check:
            reason = no_check.group(1).strip()
            if len(reason) < MIN_NO_CHECK_REASON:
                problems.append(
                    f"no-check reason < {MIN_NO_CHECK_REASON} chars: {bullet[:100]}"
                )
        elif not target or not CHECK_TOKEN_RE.search(target):
            problems.append(f"mapping does not name a check: {bullet[:100]}")
    if problems:
        return False, ["correction_checks: " + p for p in problems]
    return True, [f"correction_checks: {len(bullets)} finding(s) mapped"]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--warn-only", action="store_true")
    args = ap.parse_args(argv)
    ok, messages = check(args.root.resolve())
    for message in messages:
        print(("✅ " if ok else "⚠️  ") + message)
    return 0 if ok or args.warn_only else 1


if __name__ == "__main__":
    sys.exit(main())
