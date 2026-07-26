#!/usr/bin/env python3
"""Scope governor helpers for ship/review (inspired by openclaw autoreview ideas).

Pure classification — no network, no model calls.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class ScopeBaseline:
    """Frozen view of the change under review."""

    base_ref: str
    head_ref: str
    files: list[str]
    n_files: int
    n_insertions: int
    n_deletions: int
    non_test_loc: int
    prose_only: bool


_TEST_PATH = re.compile(
    r"(^|/)(tests?|__tests__|spec)(/|$)|_test\.|\.test\.|\.spec\.|test_",
    re.I,
)
_PROSE_EXT = {".md", ".txt", ".rst", ".adoc"}
# Paths that are NOT "prose-only exception" even if .md
_USER_FACING_DOC = re.compile(
    r"(^|/)(README|CHANGELOG|INSTALL|USAGE|docs/PRODUCT|docs/SECURITY)",
    re.I,
)


def _git(repo: Path, *args: str) -> str:
    r = subprocess.run(
        ["git", *args],
        cwd=str(repo),
        capture_output=True,
        text=True,
        check=False,
    )
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip() or r.stdout.strip() or "git failed")
    return r.stdout


def is_test_path(path: str) -> bool:
    return bool(_TEST_PATH.search(path.replace("\\", "/")))


def is_prose_path(path: str) -> bool:
    p = path.replace("\\", "/")
    suf = Path(p).suffix.lower()
    if suf not in _PROSE_EXT:
        return False
    if _USER_FACING_DOC.search(p):
        return False
    # skill/internal notes often under .agents/skills or docs internal
    return True


def classify_finding(
    *,
    introduced_by_diff: bool,
    same_owner_boundary: bool,
    requires_new_contract: bool,
    critical_exception: bool = False,
) -> str:
    """Return in_scope_blocker | follow_up | stop_and_escalate."""
    if critical_exception:
        return "in_scope_blocker"
    if requires_new_contract:
        return "stop_and_escalate"
    if introduced_by_diff and same_owner_boundary:
        return "in_scope_blocker"
    if not introduced_by_diff:
        return "follow_up"
    return "follow_up"


def build_baseline(
    repo: Path,
    *,
    base: str = "HEAD~1",
    head: str = "HEAD",
) -> ScopeBaseline:
    files_out = _git(repo, "diff", "--name-only", f"{base}...{head}").strip()
    files = [f for f in files_out.splitlines() if f.strip()]
    numstat = _git(repo, "diff", "--numstat", f"{base}...{head}").strip()
    ins = dels = non_test = 0
    for line in numstat.splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        a, b, path = parts[0], parts[1], parts[2]
        if a == "-" or b == "-":
            continue
        ai, bi = int(a), int(b)
        ins += ai
        dels += bi
        if not is_test_path(path):
            non_test += ai + bi
    prose_only = bool(files) and all(is_prose_path(f) for f in files)
    return ScopeBaseline(
        base_ref=base,
        head_ref=head,
        files=files,
        n_files=len(files),
        n_insertions=ins,
        n_deletions=dels,
        non_test_loc=non_test,
        prose_only=prose_only,
    )


def should_skip_heavy_review(baseline: ScopeBaseline) -> bool:
    """True when only internal prose/docs — skip second-model / full persona theater."""
    return baseline.prose_only


# Shared large-diff thresholds (next_skill router + cross_review_gate soft gate)
LARGE_FILES = 8
LARGE_LINES = 200
LARGE_NON_TEST_LOC = 150
LARGE_PRODUCT_PATHS = 3


def is_large_baseline(
    baseline: ScopeBaseline,
    *,
    product_path_count: int = 0,
    product_prefixes_configured: bool = False,
) -> tuple[bool, str]:
    """Return (is_large, reason_detail) using the same heuristics as ship-flow.md."""
    churn = baseline.n_insertions + baseline.n_deletions
    reasons: list[str] = []
    if baseline.n_files >= LARGE_FILES:
        reasons.append(f"files={baseline.n_files}>={LARGE_FILES}")
    if churn >= LARGE_LINES:
        reasons.append(f"churn={churn}>={LARGE_LINES}")
    if baseline.non_test_loc >= LARGE_NON_TEST_LOC:
        reasons.append(f"non_test_loc={baseline.non_test_loc}>={LARGE_NON_TEST_LOC}")
    if product_prefixes_configured and product_path_count >= LARGE_PRODUCT_PATHS:
        reasons.append(f"product_paths={product_path_count}>={LARGE_PRODUCT_PATHS}")
    if reasons:
        return True, ", ".join(reasons)
    return (
        False,
        f"files={baseline.n_files} churn={churn} non_test_loc={baseline.non_test_loc} "
        f"product_paths={product_path_count}",
    )


def scope_growth_exceeded(
    original: ScopeBaseline,
    current: ScopeBaseline,
    *,
    max_factor: float = 2.0,
) -> bool:
    if original.n_files == 0:
        return current.n_files > 5
    if current.n_files > max_factor * original.n_files:
        return True
    if original.non_test_loc > 0 and current.non_test_loc > max_factor * original.non_test_loc:
        return True
    return False


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", type=Path, default=Path("."))
    ap.add_argument("--base", default="HEAD~1")
    ap.add_argument("--head", default="HEAD")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    repo = args.repo.resolve()
    try:
        b = build_baseline(repo, base=args.base, head=args.head)
    except RuntimeError as exc:
        print(f"❌ {exc}", file=sys.stderr)
        return 2
    payload: dict[str, Any] = asdict(b)
    payload["skip_heavy_review"] = should_skip_heavy_review(b)
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"files={b.n_files} +{b.n_insertions}/-{b.n_deletions} non_test_loc={b.non_test_loc}")
        print(f"prose_only={b.prose_only} skip_heavy_review={payload['skip_heavy_review']}")
        for f in b.files[:30]:
            print(f"  {f}")
        if len(b.files) > 30:
            print(f"  … +{len(b.files)-30} more")
    return 0


if __name__ == "__main__":
    sys.exit(main())
