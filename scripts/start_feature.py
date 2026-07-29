#!/usr/bin/env python3
"""Scaffold a new feature: PR_DRAFT + optional spec stub (operator front door)."""
from __future__ import annotations

import argparse
import re
from datetime import date
from pathlib import Path

WAIVERS = frozenset({"hotfix", "chore", "docs-only", "prose-only"})

PR_SKELETON = """# PR Draft: {title}

**Range:** `HEAD~N..HEAD`

## What Problem This Solves

[fill]

## Why This Change Was Made

[fill]

## User Impact

[fill]

## Evidence

[fill]

{spec_line}

## Traceability

| AC | Test / smoke |
|----|----------------|
| AC-1 | `pytest …` / product smoke |
| … | … |

## Threat notes

Required when the ship has **runtime surface** (≥2 bullets):

- Asset / trust boundary: …
- Abuse case / mitigation: …

## Red-proof

```text
red_cmd: <command that failed>
green_cmd: <command that passed>
```

## Things that look bad but are actually fine

1. …
2. …
3. …
"""

SPEC_STUB = """# {title}

- **Product:** (from product_plugin)
- **Created:** {today}
- **Status:** draft
- **Priority:** P1
- **Spec waiver:** (use start_feature --waiver instead if no full spec)

## Problem Statement

[from operator]

## Solution

[user-facing outcome]

## User Stories

1. As a …, I want …, so that …

## Acceptance Criteria

- [ ] AC-1: …
- [ ] AC-2: …
- [ ] Product smoke succeeds
- [ ] No secrets committed

## Out of Scope

- …

## Handoff

- Next: refine acceptance → `/execute_dev`
- Then: reviews → `/pr_review --validate` → release → sync_docs
"""


def _slugify(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-") or "feature"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--slug", required=True, help="short-kebab-name")
    ap.add_argument("--title", default="", help="Human title (default: slug)")
    ap.add_argument(
        "--waiver",
        default="",
        choices=["", *sorted(WAIVERS)],
        help="If set, write Spec waiver instead of Spec path",
    )
    ap.add_argument(
        "--write-spec-stub",
        action="store_true",
        help="Write .agents/specs/<date>-<slug>.md draft stub",
    )
    ap.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing PR_DRAFT.md",
    )
    args = ap.parse_args(argv)
    root = args.root.resolve()
    slug = _slugify(args.slug)
    title = args.title.strip() or slug.replace("-", " ").title()
    today = date.today().isoformat()

    spec_rel = ""
    if args.waiver:
        spec_line = f"**Spec waiver:** {args.waiver}"
    else:
        if args.write_spec_stub:
            spec_rel = f".agents/specs/{today}-{slug}.md"
            spec_path = root / spec_rel
            if not spec_path.is_file() or args.force:
                spec_path.parent.mkdir(parents=True, exist_ok=True)
                spec_path.write_text(
                    SPEC_STUB.format(title=title, today=today), encoding="utf-8"
                )
                print(f"✅ wrote {spec_path}")
            else:
                print(f"= exists {spec_path}")
            spec_line = f"**Spec:** `{spec_rel}`"
        else:
            spec_line = (
                f"**Spec:** `.agents/specs/{today}-{slug}.md`  "
                f"<!-- create with --write-spec-stub or /spec -->"
            )

    pr = root / "PR_DRAFT.md"
    if pr.is_file() and not args.force:
        print("= PR_DRAFT.md exists (use --force to overwrite)")
        # ensure Spec line present
        text = pr.read_text(encoding="utf-8", errors="replace")
        if "**Spec" not in text and "**Spec waiver" not in text:
            pr.write_text(spec_line + "\n\n" + text, encoding="utf-8")
            print(f"✅ prepended Spec line to {pr}")
    else:
        pr.write_text(
            PR_SKELETON.format(title=title, spec_line=spec_line), encoding="utf-8"
        )
        print(f"✅ wrote {pr}")

    print()
    print("Next:")
    if not args.waiver and not args.write_spec_stub:
        print(f"  /spec refine acceptance for {slug}")
        print(f"  or: python3 scripts/start_feature.py --slug {slug} --write-spec-stub")
    print("  python3 scripts/spec_gate.py --root .")
    print("  /execute_dev")
    print("  # then follow NEXT_SKILL= through /pr_review --validate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
