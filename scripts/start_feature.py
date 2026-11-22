#!/usr/bin/env python3
"""Scaffold a new feature: PR_DRAFT + optional spec stub (operator front door)."""
from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from gate_conventions import WAIVER_MARKER, WAIVERS  # noqa: E402

# E17: size the slice before opening the window. The tree is deliberately
# boring: a huge first slice is a review and revert risk, not ambition.
DIFF_SIZE_TREE = {
    "small": "≤3 files and ≤100 changed lines — one reviewable slice",
    "medium": "≤8 files and ≤400 changed lines — split by surface if wider",
    "huge": ">8 files or >400 changed lines — split before opening the window",
}
TICKET_STUB = """# 01 — {title}

**What to build:** {title}

**depends_on:** None
**Status:** ready-for-agent

- [ ] First tracer bullet: the smallest end-to-end path that proves the shape
- [ ] Follow-on slices (split here while the diff is still small)

## Acceptance

- [ ] AC-1: …
"""

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
- {waiver_marker} (use start_feature --waiver instead if no full spec)

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


def classify_diff_size(files: int, lines: int) -> tuple[str, str]:
    """E17 — return (size, guidance) for a planned first slice."""
    if files <= 3 and lines <= 100:
        return "small", DIFF_SIZE_TREE["small"]
    if files <= 8 and lines <= 400:
        return "medium", DIFF_SIZE_TREE["medium"]
    return "huge", DIFF_SIZE_TREE["huge"]


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
    ap.add_argument(
        "--ticket-stub",
        action="store_true",
        help="Write a tracer-bullet ticket with a depends_on edge",
    )
    ap.add_argument(
        "--estimate-files",
        type=int,
        default=None,
        help="Planned file count for the diff-size decision tree",
    )
    ap.add_argument(
        "--estimate-lines",
        type=int,
        default=None,
        help="Planned changed-line count for the diff-size decision tree",
    )
    args = ap.parse_args(argv)
    root = args.root.resolve()
    slug = _slugify(args.slug)
    title = args.title.strip() or slug.replace("-", " ").title()
    today = date.today().isoformat()

    spec_rel = ""
    if args.waiver:
        spec_line = f"{WAIVER_MARKER} {args.waiver}"
    else:
        if args.write_spec_stub:
            spec_rel = f".agents/specs/{today}-{slug}.md"
            spec_path = root / spec_rel
            if not spec_path.is_file() or args.force:
                spec_path.parent.mkdir(parents=True, exist_ok=True)
                spec_path.write_text(
                    SPEC_STUB.format(
                        title=title, today=today, waiver_marker=WAIVER_MARKER
                    ),
                    encoding="utf-8",
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

    if args.ticket_stub:
        ticket_dir = root / ".agents" / "tickets" / slug
        ticket = ticket_dir / f"01-{slug}.md"
        if not ticket.is_file() or args.force:
            ticket_dir.mkdir(parents=True, exist_ok=True)
            ticket.write_text(TICKET_STUB.format(title=title), encoding="utf-8")
            print(f"✅ wrote {ticket}")

    if args.estimate_files is not None or args.estimate_lines is not None:
        size, guidance = classify_diff_size(
            max(0, args.estimate_files or 0), max(0, args.estimate_lines or 0)
        )
        print(f"diff size: {size} — {guidance}")

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
