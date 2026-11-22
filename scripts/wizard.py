#!/usr/bin/env python3
"""Generate a wizard for human-only provisioning steps (E23).

Some steps cannot be automated in this repo: creating a DNS record, clicking
through a console, rotating a credential a human holds. A wizard is a checked-in
markdown runbook with preconditions, exact steps, verification, and rollback —
so the human can execute it without rereading the chat transcript.

Usage::

  python3 scripts/wizard.py new --slug dns-cutover --title "DNS cutover" \
      --step "Create A record app.example.com → 203.0.113.10" \
      --step "Wait for TTL 300s, then curl -I https://app.example.com"
  python3 scripts/wizard.py list
"""
from __future__ import annotations

import argparse
import re
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WIZARD_DIR = Path("docs") / "wizards"


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "wizard"


def build_wizard(
    title: str,
    steps: list[str],
    *,
    owner: str = "CEO",
    deadline: str = "",
    prerequisites: list[str] | None = None,
) -> str:
    stamp = datetime.now(UTC).strftime("%Y-%m-%d")
    lines = [
        f"# Wizard — {title}",
        "",
        f"**Owner:** {owner}  ",
        f"**Created:** {stamp}  ",
        f"**Deadline:** {deadline or 'none (do before the next release)'}",
        "",
        "This is a human-only runbook. Do not paste secrets into this file.",
        "",
        "## Preconditions",
        "",
    ]
    lines.extend(f"- [ ] {item}" for item in (prerequisites or ["Access to the console/account named above"]))
    lines.extend(["", "## Steps", ""])
    for index, step in enumerate(steps, 1):
        lines.append(f"{index}. [ ] {step}")
    lines.extend(
        [
            "",
            "## Verify",
            "",
            "- [ ] Run the verification command or check the visible result.",
            "- [ ] Record the evidence path/link in the PR body.",
            "",
            "## Rollback",
            "",
            "- [ ] Undo step 1 in reverse order; note the command or console action.",
            "",
            "## Handoff",
            "",
            "When done, comment the evidence link on the shipping PR and close the ticket.",
            "",
        ]
    )
    return "\n".join(lines)


def write_wizard(
    slug: str,
    title: str,
    steps: list[str],
    *,
    root: Path = ROOT,
    owner: str = "CEO",
    deadline: str = "",
    prerequisites: list[str] | None = None,
) -> Path:
    if not steps:
        raise ValueError("at least one --step is required")
    path = root / WIZARD_DIR / f"{_slugify(slug)}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        build_wizard(
            title or slug,
            steps,
            owner=owner,
            deadline=deadline,
            prerequisites=prerequisites,
        ),
        encoding="utf-8",
    )
    return path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    new = sub.add_parser("new")
    new.add_argument("--slug", required=True)
    new.add_argument("--title", default="")
    new.add_argument("--step", action="append", default=[])
    new.add_argument("--prerequisite", action="append", default=[])
    new.add_argument("--owner", default="CEO")
    new.add_argument("--deadline", default="")
    new.add_argument("--root", type=Path, default=ROOT)
    listing = sub.add_parser("list")
    listing.add_argument("--root", type=Path, default=ROOT)
    args = ap.parse_args(argv)

    if args.cmd == "list":
        base = args.root / WIZARD_DIR
        for path in sorted(base.glob("*.md")) if base.is_dir() else []:
            print(path.relative_to(args.root))
        return 0

    try:
        path = write_wizard(
            args.slug,
            args.title or args.slug,
            args.step,
            root=args.root,
            owner=args.owner,
            deadline=args.deadline,
            prerequisites=args.prerequisite,
        )
    except ValueError as exc:
        print(f"❌ {exc}")
        return 1
    print(f"✅ wizard written: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
