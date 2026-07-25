#!/usr/bin/env python3
"""Diff-scoped secret scan for ship closeout (soft by default).

Inspired by openclaw autoreview's TruffleHog-on-bundle idea, without requiring
that binary. Order:

1. If ``gitleaks`` or ``trufflehog`` is on PATH → run on the git diff range.
2. Else run a **conservative** regex scan on added lines only (high-signal patterns).
3. Exit 0 with WARN if no scanner and soft mode; exit 1 on findings when ``--strict``.

Usage::

  python3 scripts/check_secrets_diff.py --base HEAD~1 --head HEAD
  python3 scripts/check_secrets_diff.py --strict
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path


# High-signal only (avoid password-like false positives)
_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("aws_access_key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("github_pat", re.compile(r"ghp_[A-Za-z0-9]{36,}")),
    ("github_fine_grained", re.compile(r"github_pat_[A-Za-z0-9_]{20,}")),
    ("slack_token", re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}")),
    ("private_key_header", re.compile(r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("generic_api_key_assign", re.compile(
        r"(?i)(api[_-]?key|secret[_-]?key|access[_-]?token)\s*[:=]\s*['\"][A-Za-z0-9_\-]{20,}['\"]"
    )),
]


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(repo),
        capture_output=True,
        text=True,
        check=False,
    )


def run_gitleaks(repo: Path, base: str, head: str) -> tuple[int, str]:
    bin_path = shutil.which("gitleaks")
    if not bin_path:
        return -1, ""
    # gitleaks git --log-opts
    r = subprocess.run(
        [bin_path, "git", f"--log-opts={base}..{head}", "--no-banner", "-v"],
        cwd=str(repo),
        capture_output=True,
        text=True,
        check=False,
    )
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def run_trufflehog(repo: Path, base: str, head: str) -> tuple[int, str]:
    bin_path = shutil.which("trufflehog")
    if not bin_path:
        return -1, ""
    r = subprocess.run(
        [
            bin_path,
            "git",
            f"file://{repo}",
            f"--since-commit={base}",
            f"--branch={head}",
            "--fail",
            "--only-verified",
        ],
        cwd=str(repo),
        capture_output=True,
        text=True,
        check=False,
    )
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def scan_added_lines_regex(repo: Path, base: str, head: str) -> list[str]:
    r = _git(repo, "diff", "-U0", f"{base}...{head}")
    if r.returncode != 0:
        return [f"git diff failed: {r.stderr.strip()}"]
    findings: list[str] = []
    path = ""
    for line in (r.stdout or "").splitlines():
        if line.startswith("+++ b/"):
            path = line[6:]
            continue
        if not line.startswith("+") or line.startswith("+++"):
            continue
        content = line[1:]
        for name, pat in _PATTERNS:
            if pat.search(content):
                findings.append(f"{path}: possible {name}: {content.strip()[:80]}")
    return findings


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", type=Path, default=Path("."))
    ap.add_argument("--base", default="HEAD~1")
    ap.add_argument("--head", default="HEAD")
    ap.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 on findings; also exit 1 if no external scanner and regex finds nothing? "
        "No — strict only fails on findings. Missing scanner stays soft unless --require-scanner.",
    )
    ap.add_argument(
        "--require-scanner",
        action="store_true",
        help="Fail if neither gitleaks nor trufflehog is installed",
    )
    args = ap.parse_args(argv)
    repo = args.repo.resolve()

    # Prefer external scanners
    for name, runner in (("gitleaks", run_gitleaks), ("trufflehog", run_trufflehog)):
        code, out = runner(repo, args.base, args.head)
        if code < 0:
            continue
        if code == 0:
            print(f"✅ {name}: clean ({args.base}..{args.head})")
            return 0
        print(f"❌ {name}: findings\n{out[:4000]}", file=sys.stderr)
        return 1  # external scanner findings always fail closed

    if args.require_scanner:
        print(
            "❌ neither gitleaks nor trufflehog on PATH "
            "(install one or omit --require-scanner)",
            file=sys.stderr,
        )
        return 1

    print("⚠️  no gitleaks/trufflehog — falling back to regex scan of added lines")
    findings = scan_added_lines_regex(repo, args.base, args.head)
    if findings:
        print("❌ regex secret scan findings:", file=sys.stderr)
        for f in findings[:50]:
            print(f"  {f}", file=sys.stderr)
        return 1  # high-signal patterns always fail closed
    print(f"✅ regex secret scan clean ({args.base}..{args.head})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
