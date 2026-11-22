#!/usr/bin/env python3
"""Single source of gate conventions shared by every gate script.

Before this module each gate copied its own ``**Spec:**`` / ``**Spec waiver:**``
regex. Copies drift: a new waiver type or a marker tweak landed in one gate and
missed the rest. Gate scripts import the patterns and helpers from here.

The waiver marker literal lives in this file only. Other modules build the
human-readable form with :func:`waiver_label` so a source scan can prove that
no gate re-declares the convention.
"""
from __future__ import annotations

import re

SPEC_MARKER = "**Spec:**"
WAIVER_MARKER = "**Spec waiver:**"
WAIVERS = frozenset({"hotfix", "chore", "docs-only", "prose-only"})

# Raw patterns are public so callers can embed them in larger expressions.
SPEC_PATTERN = r"\*\*Spec:\*\*\s*(\S+)"
WAIVER_PATTERN = r"\*\*Spec waiver:\*\*\s*(hotfix|chore|docs-only|prose-only)\b"
SPEC_RE = re.compile(SPEC_PATTERN, re.IGNORECASE)
WAIVER_RE = re.compile(WAIVER_PATTERN, re.IGNORECASE)


def spec_path(text: str) -> str | None:
    """Return the linked Spec path from a PR draft, or None."""
    match = SPEC_RE.search(text or "")
    if not match:
        return None
    return match.group(1).strip().strip("`")


def waiver_type(text: str) -> str | None:
    """Return the declared waiver type from a PR draft, or None."""
    match = WAIVER_RE.search(text or "")
    return match.group(1).lower() if match else None


def is_waiver(text: str) -> bool:
    return waiver_type(text) in WAIVERS


def waiver_label(kind: str) -> str:
    """Build the PR-draft waiver line without repeating the marker literal."""
    return f"{WAIVER_MARKER} {kind}"


def waiver_choice_hint() -> str:
    return "|".join(sorted(WAIVERS))


__all__ = [
    "SPEC_MARKER",
    "WAIVER_MARKER",
    "WAIVERS",
    "SPEC_PATTERN",
    "WAIVER_PATTERN",
    "SPEC_RE",
    "WAIVER_RE",
    "spec_path",
    "waiver_type",
    "is_waiver",
    "waiver_label",
    "waiver_choice_hint",
]
