#!/usr/bin/env python3
"""Smart-zone token guard for implementer subagents (E18).

A subagent stays in the "smart zone" while its working context is roughly
150k tokens. Past that budget, quality drops silently. The guard estimates
tokens from a file or a character count and, past the budget, returns an
externalization plan: write decisions, spec, tickets, and open questions to
artifacts, then continue from a fresh context.

This module never calls a model. The caller decides when to compact.

Usage::

  python3 scripts/smart_zone_guard.py --chars 720000
  python3 scripts/smart_zone_guard.py --file .agents/artifacts/PLAN.md
"""
from __future__ import annotations

import argparse
from pathlib import Path

# ~150k tokens: the point where a single implementer context starts to lose
# earlier decisions. Keep the literal in one place.
SMART_ZONE_TOKENS = 150_000
CHARS_PER_TOKEN = 4
EXTERNALIZE_ARTIFACTS = (
    ".agents/artifacts/DECISIONS.md",
    ".agents/artifacts/OPEN_QUESTIONS.md",
    ".agents/specs/<spec>.md",
    ".agents/tickets/<slug>/",
)


def estimate_tokens(text: str) -> int:
    """Cheap, deterministic estimate: one token per four characters."""
    return (len(text) + CHARS_PER_TOKEN - 1) // CHARS_PER_TOKEN


def zone_state(tokens: int) -> str:
    if tokens <= SMART_ZONE_TOKENS:
        return "inside"
    return "externalize"


def externalization_plan(tokens: int) -> list[str]:
    """Steps to run when the context is past the smart zone."""
    if tokens <= SMART_ZONE_TOKENS:
        return [f"inside smart zone ({tokens:,}/{SMART_ZONE_TOKENS:,} tokens)"]
    return [
        f"past smart zone ({tokens:,}/{SMART_ZONE_TOKENS:,} tokens)",
        "externalize decisions to " + EXTERNALIZE_ARTIFACTS[0],
        "externalize open questions to " + EXTERNALIZE_ARTIFACTS[1],
        "externalize spec + tickets to " + EXTERNALIZE_ARTIFACTS[2]
        + " and " + EXTERNALIZE_ARTIFACTS[3],
        "start a fresh implementer context that reads those artifacts first",
        "do not keep summarizing in the same context; write it down and restart",
    ]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--file", type=Path, action="append", default=[])
    ap.add_argument("--chars", type=int, default=0)
    args = ap.parse_args(argv)
    chars = max(0, args.chars)
    for path in args.file:
        chars += len(path.read_text(encoding="utf-8", errors="replace"))
    tokens = (chars + CHARS_PER_TOKEN - 1) // CHARS_PER_TOKEN
    print(f"tokens≈{tokens:,} (chars={chars:,}) · budget={SMART_ZONE_TOKENS:,}")
    for step in externalization_plan(tokens):
        print(f"- {step}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
