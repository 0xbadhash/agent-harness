#!/usr/bin/env python3
"""Soft gate: large diffs should have a cross_review artifact before pr_review.

Does **not** block approval by default (soft). Use --strict to exit 1 when missing.

Evidence of cross_review (any one):
  - PR_DRAFT.md contains 'CROSS-REVIEW' or '## Cross-review'
  - .agents/artifacts/CROSS_REVIEW.md exists and is non-empty

Large diff heuristic (shared with next_skill via review_scope.is_large_baseline):
  - changed file count >= LARGE_FILES (default 8)
  - insertions+deletions >= LARGE_LINES (default 200)
  - non-test LOC >= LARGE_NON_TEST_LOC (default 150)
  - >=3 paths under product_plugin.product_path_prefixes (stack-agnostic)
"""
from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

from product_plugin import (  # type: ignore
    load_product_path_prefixes,
    path_matches_product_prefixes,
)
from review_scope import (  # type: ignore
    LARGE_FILES,
    LARGE_LINES,
    ScopeBaseline,
    is_large_baseline,
    is_test_path,
)

ROOT = Path(__file__).resolve().parent.parent
PR_DRAFT = ROOT / "PR_DRAFT.md"
CROSS_ARTIFACT = ROOT / ".agents" / "artifacts" / "CROSS_REVIEW.md"
_UNSET = object()


def _git_diff_stat(diff: str | None) -> tuple[list[str], int, int]:
    """Return (paths, total_line_churn, non_test_loc)."""
    cmd = ["git", "diff", "--numstat"]
    if diff:
        cmd.append(diff)
    else:
        # Three-dot merge-base range — matches review_scope / check_secrets_diff
        cmd.append("HEAD~1...HEAD")
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False)
    if r.returncode != 0:
        return [], 0, 0
    paths: list[str] = []
    churn = 0
    non_test = 0
    for line in r.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        a, b, path = parts[0], parts[1], parts[2]
        if a == "-" or b == "-":
            paths.append(path)
            continue
        try:
            ai, bi = int(a), int(b)
            churn += ai + bi
            if not is_test_path(path):
                non_test += ai + bi
        except ValueError:
            pass
        paths.append(path)
    return paths, churn, non_test


def has_cross_review_evidence(
    pr_draft: Path = PR_DRAFT,
    *,
    artifact: Path | None | object = _UNSET,
) -> bool:
    art: Path | None
    if artifact is _UNSET:
        art = CROSS_ARTIFACT
    else:
        art = artifact  # type: ignore[assignment]
    if art is not None and art.is_file() and art.read_text(encoding="utf-8").strip():
        return True
    if pr_draft.is_file():
        text = pr_draft.read_text(encoding="utf-8")
        if re.search(r"CROSS-REVIEW|##\s*Cross-review", text, re.I):
            return True
    return False


def is_large_diff(diff: str | None) -> tuple[bool, str]:
    paths, churn, non_test = _git_diff_stat(diff)
    n = len(paths)
    prefixes = load_product_path_prefixes(ROOT)
    product = [p for p in paths if path_matches_product_prefixes(p, prefixes)]
    # Reconstruct a minimal baseline so thresholds match next_skill / review_scope
    baseline = ScopeBaseline(
        base_ref="base",
        head_ref="head",
        files=paths,
        n_files=n,
        n_insertions=churn,  # combined; only sum is used by is_large_baseline
        n_deletions=0,
        non_test_loc=non_test,
        prose_only=False,
    )
    large, detail = is_large_baseline(
        baseline,
        product_path_count=len(product),
        product_prefixes_configured=bool(prefixes),
    )
    if large:
        return True, detail
    return (
        False,
        f"{detail} prefixes={len(prefixes)} (thresholds files>={LARGE_FILES} "
        f"churn>={LARGE_LINES})",
    )


def evaluate(
    diff: str | None = None,
    pr_draft: Path = PR_DRAFT,
    *,
    artifact: Path | None | object = _UNSET,
) -> dict:
    large, detail = is_large_diff(diff)
    evidence = has_cross_review_evidence(pr_draft, artifact=artifact)
    warn = large and not evidence
    return {
        "large": large,
        "detail": detail,
        "evidence": evidence,
        "soft_warn": warn,
        "message": (
            "⚠️ CROSS_REVIEW soft-gate: large diff without CROSS-REVIEW evidence. "
            "Run /cross_review and record in PR_DRAFT or .agents/artifacts/CROSS_REVIEW.md"
            if warn
            else (
                "✅ cross_review evidence present"
                if evidence
                else "✅ cross_review soft-gate N/A (diff not large)"
            )
        ),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Soft cross_review gate for pr_review")
    ap.add_argument("--diff", help="Git range (default HEAD~1...HEAD three-dot)")
    ap.add_argument("--pr-draft", type=Path, default=PR_DRAFT)
    ap.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 if large diff lacks evidence (hard gate)",
    )
    args = ap.parse_args(argv)
    result = evaluate(args.diff, args.pr_draft)
    print(result["message"])
    print(
        f"  large={result['large']} evidence={result['evidence']} ({result['detail']})"
    )
    if args.strict and result["soft_warn"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
