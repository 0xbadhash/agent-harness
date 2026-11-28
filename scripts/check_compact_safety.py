#!/usr/bin/env python3
"""Compact-safety gate: do not compact until the work is on disk (E19).

Compaction is lossy. Before it runs, the session must have:

- a linked **Spec** path that exists,
- at least one ticket file (the tracer bullets),
- a glossary entry for the domain terms the spec introduces.

If any is missing, the answer is "write it down first", not "compact and hope".

Usage::

  python3 scripts/check_compact_safety.py --root .
  python3 scripts/check_compact_safety.py --root . --json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from gate_conventions import SPEC_RE  # noqa: E402

TICKETS_RE = re.compile(r"\*\*Tickets:\*\*\s*(\S+)", re.IGNORECASE)
GLOSSARY_PATHS = ("GLOSSARY.md", "docs/GLOSSARY.md", "docs/glossary.md")


def _tickets(root: Path, draft: str, spec_path: Path | None) -> list[Path]:
    match = TICKETS_RE.search(draft)
    if match:
        candidate = root / match.group(1).strip().strip("`")
        return sorted(candidate.glob("*.md")) if candidate.is_dir() else []
    if spec_path is not None:
        sibling = spec_path.parent / spec_path.stem / "tickets"
        if sibling.is_dir():
            return sorted(sibling.glob("*.md"))
    return []


def check(root: Path, pr_draft: Path | None = None) -> tuple[bool, list[str]]:
    root = Path(root).resolve()
    draft_path = pr_draft or (root / "PR_DRAFT.md")
    draft = (
        draft_path.read_text(encoding="utf-8", errors="replace")
        if draft_path.is_file()
        else ""
    )
    missing: list[str] = []

    match = SPEC_RE.search(draft)
    spec_path: Path | None = None
    if not match:
        missing.append("no linked Spec (**Spec:** <path>) in PR_DRAFT")
    else:
        spec_path = (root / match.group(1).strip().strip("`")).resolve()
        if not spec_path.is_file():
            missing.append(f"Spec path does not exist: {match.group(1).strip()}")
            spec_path = None

    tickets = _tickets(root, draft, spec_path)
    if not tickets:
        missing.append("no ticket file on disk (create .agents/tickets/<slug>/01-*.md)")

    glossary = next((root / rel for rel in GLOSSARY_PATHS if (root / rel).is_file()), None)
    if glossary is None:
        missing.append("no glossary file — define domain terms before compaction")

    if missing:
        return False, ["compact blocked: " + item for item in missing]
    return True, [
        f"ok: compact safe — spec={spec_path.name if spec_path else '?'}, "
        f"tickets={len(tickets)}, glossary={glossary.name if glossary else '?'}"
    ]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--pr-draft", type=Path, default=None)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    ok, messages = check(args.root, args.pr_draft)
    if args.json:
        print(json.dumps({"ok": ok, "messages": messages}, indent=2))
    else:
        for message in messages:
            print(("✅ " if ok else "❌ ") + message)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
