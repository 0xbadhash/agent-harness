#!/usr/bin/env python3
"""Disposable prototype variants for design questions (E22).

When a grill question is "which shape should this take?", prose debate is the
slowest answer. Write two or three throwaway variants, each with one opinionated
difference, pick one in the grill, and delete the rest before implementation.

Variants are written under ``.agents/prototypes/<slug>/`` and are explicitly
**DO NOT SHIP**. They are sketches, not a branch to merge.

Usage::

  python3 scripts/prototype_variants.py new --slug cache-shape \
      --question "Cache by ticker or by portfolio snapshot?" --variants 3
  python3 scripts/prototype_variants.py list
"""
from __future__ import annotations

import argparse
import re
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DIR = Path(".agents") / "prototypes"
LENSES = (
    ("a", "Simplest possible shape", "What is the least code that answers the question?"),
    ("b", "Inverted assumption", "What if the opposite assumption is true?"),
    ("c", "Operational shape", "What survives a restart, a bad input, and a reviewer?"),
)


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "prototype"


def _variant_text(slug: str, question: str, key: str, lens: str, prompt: str) -> str:
    return f"""# Prototype {slug} — variant {key}: {lens}

**DO NOT SHIP. Disposable sketch. Delete before implementation.**

**Question:** {question}
**Lens:** {prompt}
**Created:** {datetime.now(UTC):%Y-%m-%d}

## Sketch

[smallest sketch that answers the lens — a route, a function signature, or a screen]

## What this variant proves

- …

## What it costs

- …

## Kill criterion

If this variant does not change the grill decision in 30 minutes, stop.
"""


def make_variants(
    question: str,
    *,
    slug: str = "",
    variants: int = 3,
    root: Path = ROOT,
    out_dir: Path | None = None,
) -> list[Path]:
    if not question.strip():
        raise ValueError("question is required")
    count = max(2, min(3, variants))
    slug = _slugify(slug or question)
    base = (out_dir or (root / DEFAULT_DIR / slug)).resolve()
    base.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for key, lens, prompt in LENSES[:count]:
        path = base / f"variant-{key}.md"
        path.write_text(_variant_text(slug, question, key, lens, prompt), encoding="utf-8")
        written.append(path)
    return written


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    new = sub.add_parser("new")
    new.add_argument("--slug", default="")
    new.add_argument("--question", required=True)
    new.add_argument("--variants", type=int, default=3)
    new.add_argument("--root", type=Path, default=ROOT)
    listing = sub.add_parser("list")
    listing.add_argument("--root", type=Path, default=ROOT)
    args = ap.parse_args(argv)

    if args.cmd == "list":
        base = args.root / DEFAULT_DIR
        for path in sorted(base.glob("*/variant-*.md")) if base.is_dir() else []:
            print(path.relative_to(args.root))
        return 0

    try:
        paths = make_variants(
            args.question,
            slug=args.slug,
            variants=args.variants,
            root=args.root,
        )
    except ValueError as exc:
        print(f"❌ {exc}")
        return 1
    for path in paths:
        print(f"✅ wrote {path}")
    print("Pick one in the grill, record why, then delete the prototype directory.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
