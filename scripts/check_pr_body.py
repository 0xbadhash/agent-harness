#!/usr/bin/env python3
"""PR-body gate: smallest slice, before/after evidence, merge-danger call.

The body has to answer three questions a reviewer cannot infer from the diff:

1. **Smallest** — what is the smallest visual/behavioral change that proves the
   slice? (A giant PR with no answer is a review hazard.)
2. **Before/after** — what did the user see before, and what do they see now?
3. **Merge danger** — is the merge one-way (hard to undo) or two-way
   (revertible)? Say which, and why.

Usage::

  python3 scripts/check_pr_body.py --root .
  python3 scripts/check_pr_body.py --root . --pr-draft PR_DRAFT.md
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from gate_conventions import waiver_type  # noqa: E402

SMALLEST_RE = re.compile(r"\bsmallest\b", re.IGNORECASE)
BEFORE_RE = re.compile(r"\bbefore\b", re.IGNORECASE)
AFTER_RE = re.compile(r"\bafter\b", re.IGNORECASE)
ONE_WAY_RE = re.compile(r"\bone[\s-]?way\b", re.IGNORECASE)
TWO_WAY_RE = re.compile(r"\btwo[\s-]?way\b", re.IGNORECASE)
EVIDENCE_HINT_RE = re.compile(r"(https?://|!\[|```|`[^`]+`|\|.+\|)", re.IGNORECASE)


def _section(text: str, name: str) -> str:
    match = re.search(
        rf"^##+\s+{re.escape(name)}\b(.*?)(?=^##+\s|\Z)",
        text,
        re.IGNORECASE | re.MULTILINE | re.DOTALL,
    )
    return match.group(1).strip() if match else ""


def check(root: Path, pr_draft: Path | None = None) -> tuple[bool, list[str]]:
    root = Path(root).resolve()
    draft_path = pr_draft or (root / "PR_DRAFT.md")
    if not draft_path.is_file():
        return False, [f"PR body missing: {draft_path}"]
    text = draft_path.read_text(encoding="utf-8", errors="replace")

    # Docs-only/prose-only ships have no visual surface to summarize.
    if waiver_type(text) in {"docs-only", "prose-only"}:
        return True, ["ok: docs/prose waiver — PR body gate skipped"]

    msgs: list[str] = []
    failures: list[str] = []

    smallest = _section(text, "Smallest") or _section(text, "Smallest visual change")
    if not smallest:
        failures.append(
            "add `## Smallest visual change` naming the smallest slice that proves "
            "the behavior (one screen, one command, or one route)"
        )
    elif not SMALLEST_RE.search(smallest) or len(smallest) < 40:
        failures.append(
            "`## Smallest visual change` needs the word 'smallest' plus a concrete "
            "slice (≥40 characters)"
        )

    before_after = _section(text, "Before/after") or _section(text, "Before / after")
    if not before_after:
        failures.append(
            "add `## Before/after` with both the old and new evidence "
            "(screenshot, curl output, or diff snippet)"
        )
    else:
        if not BEFORE_RE.search(before_after):
            failures.append("`## Before/after` must state the **before** evidence")
        if not AFTER_RE.search(before_after):
            failures.append("`## Before/after` must state the **after** evidence")
        if not EVIDENCE_HINT_RE.search(before_after):
            failures.append(
                "`## Before/after` needs concrete evidence (link, image, code block, "
                "or table) — prose alone is not evidence"
            )

    danger = _section(text, "Merge danger")
    if not danger:
        failures.append(
            "add `## Merge danger` with an explicit one-way or two-way call and why"
        )
    elif not (ONE_WAY_RE.search(danger) or TWO_WAY_RE.search(danger)):
        failures.append(
            "`## Merge danger` must say 'one-way' (hard to undo) or 'two-way' "
            "(revertible by reverting the merge)"
        )

    if failures:
        return False, failures
    kind = "one-way" if ONE_WAY_RE.search(danger) else "two-way"
    msgs.append(f"ok: smallest slice + before/after evidence + {kind} merge call")
    return True, msgs


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--pr-draft", type=Path, default=None)
    args = ap.parse_args(argv)
    ok, msgs = check(args.root, args.pr_draft)
    for message in msgs:
        print(("✅ " if ok else "❌ ") + message)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
