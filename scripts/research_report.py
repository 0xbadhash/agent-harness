#!/usr/bin/env python3
"""Research report: turn local notes into a cited repo artifact (E24).

The research skill collects notes from primary sources. This script is the
deterministic part: every bullet claim must carry a ``Source:`` line (or an
inline markdown link), and the output lands in ``docs/research/`` so the next
reader can check the claim instead of trusting the summary.

Offline: this script never fetches a URL. The sources are whatever the notes
already recorded.

Usage::

  python3 scripts/research_report.py --question "Which gate misses drift?" \\
      --notes notes.md --slug fork-drift --strict
  python3 scripts/research_report.py --question "..." --notes notes.md --dry-run
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = Path("docs") / "research"

BULLET_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(.+)$")
SOURCE_RE = re.compile(r"^\s*(?:[>*-]\s*)?(?:\*\*)?source(?:\*\*)?\s*:\s*(.+)$", re.IGNORECASE)
CITATION_RE = re.compile(r"\[[^\]]+\]\((https?://[^)\s]+)\)")


@dataclass(frozen=True)
class Claim:
    text: str
    source: str

    @property
    def cited(self) -> bool:
        return bool(self.source.strip())


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "research"


def parse_claims(notes: str) -> list[Claim]:
    """Split notes into bullet claims, attaching the nearest source line.

    A bullet starts a claim. Indented continuation lines join that claim; a
    ``Source:`` line or an inline link supplies its citation. Blank lines close
    the claim. Introductory prose outside bullets is not treated as a claim.
    """
    claims: list[Claim] = []
    current: list[str] = []
    source = ""

    def flush() -> None:
        nonlocal current, source
        if current:
            claims.append(Claim(" ".join(current).strip(), source.strip()))
        current, source = [], ""

    for raw in notes.splitlines():
        line = raw.strip()
        if not line:
            flush()
            continue
        src = SOURCE_RE.match(line)
        if src:
            source = src.group(1).strip()
            continue
        bullet = BULLET_RE.match(line)
        if bullet:
            flush()
            current = [bullet.group(1).strip()]
            cite = CITATION_RE.search(bullet.group(1))
            if cite:
                source = cite.group(1)
            continue
        if current:
            cite = CITATION_RE.search(line)
            if cite and not source:
                source = cite.group(1)
            current.append(line)
    flush()
    return claims


def uncited(claims: list[Claim]) -> list[str]:
    return [claim.text for claim in claims if not claim.cited]


def build_report(
    question: str,
    claims: list[Claim],
    *,
    when: datetime | None = None,
) -> str:
    when = when or datetime.now(UTC)
    cited = sum(1 for claim in claims if claim.cited)
    lines = [
        f"# Research — {question or 'untitled'}",
        "",
        f"**Date:** {when:%Y-%m-%d}  ",
        "**Mode:** offline notes, no live fetch  ",
        f"**Claims:** {len(claims)} · **Cited:** {cited}/{len(claims)}",
        "",
        "## Question",
        "",
        question or "(not stated)",
        "",
        "## Findings",
        "",
    ]
    if not claims:
        lines.append("_No bullet claims were extracted. Add one bullet per claim._")
    for claim in claims:
        lines.append(f"- {claim.text}")
        if claim.cited:
            lines.append(f"  - Source: {claim.source}")
        else:
            lines.append("  - Source: ⚠️ MISSING — do not ship this claim")
    lines.extend(
        [
            "",
            "## Confidence",
            "",
            "- High: every claim has a primary source recorded above.",
            "- Medium: sources are secondary or one-sided; say what is unverified.",
            "- Low: uncited claims remain; do not act on them.",
            "",
            "## How this was produced",
            "",
            "Notes were read from disk and rendered by `scripts/research_report.py`; "
            "no network calls were made by the script.",
            "",
        ]
    )
    return "\n".join(lines)


def write_report(
    root: Path,
    slug: str,
    question: str,
    claims: list[Claim],
    *,
    out: Path | None = None,
    when: datetime | None = None,
) -> Path:
    when = when or datetime.now(UTC)
    target = out or (root / OUT_DIR / f"{when:%Y-%m-%d}-{_slugify(slug)}.md")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(build_report(question, claims, when=when), encoding="utf-8")
    return target


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--question", required=True)
    ap.add_argument("--notes", type=Path, default=None, help="notes file (stdin when omitted)")
    ap.add_argument("--slug", default="")
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--strict", action="store_true", help="fail instead of writing uncited claims")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    root = args.root.resolve()
    if args.notes is not None:
        if not args.notes.is_file():
            print(f"❌ notes file not found: {args.notes}")
            return 1
        notes = args.notes.read_text(encoding="utf-8", errors="replace")
    else:
        notes = sys.stdin.read()

    claims = parse_claims(notes)
    missing = uncited(claims)
    if args.strict and missing:
        print(f"❌ {len(missing)} uncited claim(s); add a Source: line or inline link:")
        for item in missing:
            print(f"  - {item}")
        return 1

    if args.dry_run:
        print(build_report(args.question, claims))
        return 0

    slug = args.slug or args.question
    path = write_report(root, slug, args.question, claims, out=args.out)
    cited = len(claims) - len(missing)
    print(f"✅ research written: {path} ({len(claims)} claims, {cited} cited)")
    if missing:
        print(f"⚠️  {len(missing)} claim(s) still need a source")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
