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
from typing import cast

from product_plugin import (
    load_product_path_prefixes,
    path_matches_product_prefixes,
)
from review_scope import (
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
    art: Path | None = (
        CROSS_ARTIFACT if artifact is _UNSET else cast(Path | None, artifact)
    )
    if art is not None and art.is_file() and art.read_text(encoding="utf-8").strip():
        return True
    if pr_draft.is_file():
        text = pr_draft.read_text(encoding="utf-8")
        if re.search(r"CROSS-REVIEW|##\s*Cross-review", text, re.IGNORECASE):
            return True
    return False


def is_large_diff(diff: str | None) -> tuple[bool, str]:
    raw = _git_diff_stat(diff)
    # Accept legacy 2-tuple mocks (paths, churn) used in older product tests
    if isinstance(raw, tuple) and len(raw) == 2:
        paths, churn = raw
        non_test = int(churn) if not isinstance(churn, int) else churn
        if not isinstance(non_test, int):
            non_test = 0
    else:
        paths, churn, non_test = raw
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
        product_root=ROOT,
    )
    if large:
        return True, detail
    return (
        False,
        f"{detail} prefixes={len(prefixes)} (thresholds files>={LARGE_FILES} "
        f"churn>={LARGE_LINES})",
    )


STANDARDS_AXIS = "standards"
SPEC_AXIS = "spec-fidelity"
AXES = (STANDARDS_AXIS, SPEC_AXIS)
BARE_EXCEPT_RE = re.compile(r"^\+\s*except\s*:")
TODO_RE = re.compile(r"TODO(?!\s*\(|\s*:|\s*#)")
AC_RE = re.compile(r"\bAC-(\d+)\b", re.IGNORECASE)


def _added_lines(diff: str | None) -> list[tuple[str, str]]:
    """Return (path, added_line) for a git diff range."""
    cmd = ["git", "diff", "-U0"]
    cmd.append(diff or "HEAD~1...HEAD")
    run = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False)
    if run.returncode != 0:
        return []
    out: list[tuple[str, str]] = []
    path = ""
    for line in run.stdout.splitlines():
        if line.startswith("+++ b/"):
            path = line[6:]
        elif line.startswith("+") and not line.startswith("+++"):
            out.append((path, line[1:]))
    return out


def review_standards(diff: str | None = None) -> dict:
    """Axis 1 — code standards that do not depend on the spec."""
    findings: list[str] = []
    for path, line in _added_lines(diff):
        if BARE_EXCEPT_RE.match("+" + line):
            findings.append(f"{path}: bare `except:` swallows the cause")
        if TODO_RE.search(line) and not is_test_path(path):
            findings.append(f"{path}: TODO without an owner or issue reference")
    return {
        "axis": STANDARDS_AXIS,
        "ok": not findings,
        "findings": findings,
        "message": (
            "✅ standards axis clean"
            if not findings
            else f"❌ standards axis: {len(findings)} finding(s)"
        ),
    }


def _spec_path(spec: Path | None) -> Path | None:
    if spec is not None:
        return spec if spec.is_file() else None
    if PR_DRAFT.is_file():
        match = re.search(r"\*\*Spec:\*\*\s*(\S+)", PR_DRAFT.read_text(encoding="utf-8"))
        if match:
            candidate = ROOT / match.group(1).strip().strip("`")
            return candidate if candidate.is_file() else None
    return None


def review_spec_fidelity(
    diff: str | None = None, spec: Path | None = None
) -> dict:
    """Axis 2 — does the change actually satisfy the linked spec?"""
    path = _spec_path(spec)
    if path is None:
        return {
            "axis": SPEC_AXIS,
            "ok": True,
            "findings": [],
            "message": "✅ spec axis N/A (no linked spec)",
        }
    acs = sorted({int(m.group(1)) for m in AC_RE.finditer(path.read_text(encoding="utf-8"))})
    if not acs:
        return {
            "axis": SPEC_AXIS,
            "ok": True,
            "findings": [],
            "message": f"✅ spec axis clean ({path.name} has no AC-n)",
        }
    changed = "\n".join(line for _, line in _added_lines(diff))
    tests = "\n".join(
        p.read_text(encoding="utf-8", errors="replace")
        for p in ROOT.joinpath("tests").rglob("test_*.py")
    )
    corpus = changed + "\n" + tests
    findings = [
        f"AC-{n} has no code/test reference in the diff or tests"
        for n in acs
        if not re.search(rf"\bAC-{n}\b|ac[_-]?{n}\b", corpus, re.IGNORECASE)
    ]
    return {
        "axis": SPEC_AXIS,
        "ok": not findings,
        "findings": findings,
        "message": (
            f"✅ spec axis clean ({len(acs)} AC(s) traced)"
            if not findings
            else f"❌ spec axis: {len(findings)} finding(s)"
        ),
    }


def review_axes(
    diff: str | None = None, spec: Path | None = None
) -> list[dict]:
    return [review_standards(diff), review_spec_fidelity(diff, spec)]


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
    ap.add_argument(
        "--axis",
        choices=[*AXES, "both"],
        default=None,
        help="Run one review axis instead of the artifact-presence check",
    )
    ap.add_argument("--spec", type=Path, default=None, help="Linked Spec path")
    args = ap.parse_args(argv)

    if args.axis:
        axes = review_axes(args.diff, args.spec) if args.axis == "both" else [
            review_standards(args.diff)
            if args.axis == STANDARDS_AXIS
            else review_spec_fidelity(args.diff, args.spec)
        ]
        for result in axes:
            print(result["message"])
            for finding in result["findings"]:
                print(f"  - {finding}")
        if args.strict and not all(result["ok"] for result in axes):
            return 1
        return 0

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
