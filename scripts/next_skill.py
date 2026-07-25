#!/usr/bin/env python3
"""Print a single mandatory handoff line: NEXT_SKILL=...

Used by execute_dev / code_review / cross_review / behavior_validator so agents
and humans always know the exact next slash skill.

Examples::

  python3 scripts/next_skill.py --after execute_dev --base HEAD~1 --head HEAD
  python3 scripts/next_skill.py --after code_review --base origin/main
  python3 scripts/next_skill.py --after behavior_validator

Exit 0 always when it can decide; prints exactly one NEXT_SKILL= line to stdout
(plus optional KEY= notes on stderr for humans).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from review_scope import (  # noqa: E402
    build_baseline,
    should_skip_heavy_review,
)


def _large(baseline) -> bool:
    return (
        baseline.n_files >= 8
        or (baseline.n_insertions + baseline.n_deletions) >= 200
        or baseline.non_test_loc >= 150
    )


def _runtime_surface(baseline) -> bool:
    """Heuristic: code/config that could affect running product."""
    if baseline.prose_only:
        return False
    runtime_ext = {
        ".py",
        ".ts",
        ".tsx",
        ".js",
        ".jsx",
        ".go",
        ".rs",
        ".php",
        ".sh",
        ".yaml",
        ".yml",
        ".toml",
        ".json",
        ".css",
        ".html",
        ".sql",
    }
    for f in baseline.files:
        p = f.replace("\\", "/")
        if p.endswith("SKILL.md") or "/.agents/skills/" in p:
            continue
        suf = Path(p).suffix.lower()
        if suf in runtime_ext:
            return True
        if p.startswith("src/") or p.startswith("scripts/") or p.startswith("deploy/"):
            return True
    return False


def decide(
    after: str,
    *,
    base: str,
    head: str,
    repo: Path,
    force_cross: bool = False,
    skip_behavior: bool = False,
) -> tuple[str, dict[str, str]]:
    """Return (next_skill_token, meta)."""
    after = after.strip().lstrip("/").replace("-", "_")
    meta: dict[str, str] = {"after": after}

    if after in ("behavior_validator", "behavior-validator"):
        return "/pr_review --validate", {**meta, "reason": "behavior done"}

    if after in ("pr_review", "pr-review"):
        return "/release_mgmt", {**meta, "reason": "if approved; else fix and re-validate"}

    if after in ("release_mgmt", "release-mgmt"):
        return "/sync_docs", {**meta, "reason": "after shipped"}

    if after == "sync_docs":
        return "(done)", {**meta, "reason": "cycle complete → init"}

    if after == "handoff":
        return "(continue with task)", {**meta, "reason": "handoff is not a ship step"}

    if after in ("session_viewer", "session-viewer", "agent_transcript", "agent-transcript"):
        return "(return to ship path)", {**meta, "reason": "ops skill; resume execute_dev or pr_review"}

    # Need baseline for execute_dev / code_review / cross_review
    try:
        b = build_baseline(repo, base=base, head=head)
    except Exception as exc:  # noqa: BLE001
        # Fail open to safe default
        meta["scope_error"] = str(exc)
        if after in ("execute_dev", "execute-dev"):
            return "/code_review", meta
        return "/pr_review --validate", meta

    meta["prose_only"] = str(b.prose_only)
    meta["large"] = str(_large(b))
    meta["runtime"] = str(_runtime_surface(b))
    meta["n_files"] = str(b.n_files)

    if after in ("execute_dev", "execute-dev"):
        if should_skip_heavy_review(b):
            # Small internal docs: skip code_review and cross_review
            return "/pr_review --validate", {
                **meta,
                "reason": "prose-only → skip code_review",
                "code_review": "skipped",
            }
        return "/code_review", {**meta, "reason": "non-prose code ship", "code_review": "required"}

    if after in ("code_review", "code-review"):
        if force_cross or _large(b):
            return "/cross_review", {**meta, "reason": "large/non-trivial diff"}
        if not skip_behavior and _runtime_surface(b):
            return "/behavior_validator", {
                **meta,
                "reason": "runtime surface → behavior contract check",
            }
        return "/pr_review --validate", {**meta, "reason": "small code; score next"}

    if after in ("cross_review", "cross-review"):
        if not skip_behavior and _runtime_surface(b):
            return "/behavior_validator", {
                **meta,
                "reason": "runtime surface after personas",
            }
        return "/pr_review --validate", {**meta, "reason": "no runtime surface or behavior skipped"}

    return f"/{after}", {**meta, "reason": "unknown after=; echoed"}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--after",
        required=True,
        help="Skill just finished: execute_dev|code_review|cross_review|behavior_validator|…",
    )
    ap.add_argument("--repo", type=Path, default=Path("."))
    ap.add_argument("--base", default="HEAD~1")
    ap.add_argument("--head", default="HEAD")
    ap.add_argument(
        "--force-cross",
        action="store_true",
        help="After code_review, always choose cross_review",
    )
    ap.add_argument(
        "--skip-behavior",
        action="store_true",
        help="Never route to behavior_validator",
    )
    ap.add_argument("--verbose", action="store_true", help="Print meta on stderr")
    args = ap.parse_args(argv)

    nxt, meta = decide(
        args.after,
        base=args.base,
        head=args.head,
        repo=args.repo.resolve(),
        force_cross=args.force_cross,
        skip_behavior=args.skip_behavior,
    )
    # Exactly one handoff line for agents/humans to parse
    print(f"NEXT_SKILL={nxt}")
    if args.verbose:
        for k, v in sorted(meta.items()):
            print(f"# {k}={v}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
