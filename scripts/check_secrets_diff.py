#!/usr/bin/env python3
"""Diff-scoped secret scan for ship closeout.

Inspired by openclaw autoreview's TruffleHog-on-bundle idea, without requiring
that binary. Order:

1. If ``gitleaks`` or ``trufflehog`` is on PATH → run on the git range
   ``base...head`` (three-dot / merge-base semantics, same as the regex path).
2. Else run a **conservative** regex scan on added lines only (high-signal patterns).
3. **Findings always fail closed** (exit 1), with or without ``--strict``.
4. Missing external scanner: warn + regex fallback (exit 0 only if clean).
   Use ``--require-scanner`` (or ``--strict``) to fail if neither tool is installed.

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


# High-signal only (avoid password-like false positives). HSQ-3 P0 G5: expand.
_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("aws_access_key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("github_pat", re.compile(r"ghp_[A-Za-z0-9]{36,}")),
    ("github_fine_grained", re.compile(r"github_pat_[A-Za-z0-9_]{20,}")),
    ("github_oauth", re.compile(r"gho_[A-Za-z0-9]{36,}")),
    ("slack_token", re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}")),
    ("private_key_header", re.compile(r"-----BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")),
    ("generic_api_key_assign", re.compile(
        r"(?i)(api[_-]?key|secret[_-]?key|access[_-]?token)\s*[:=]\s*['\"][A-Za-z0-9_\-]{20,}['\"]"
    )),
    # G5 tighten
    ("jwt_compact", re.compile(
        r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"
    )),
    ("openai_sk", re.compile(r"\bsk-[A-Za-z0-9]{20,}\b")),
    ("openai_sk_proj", re.compile(r"\bsk-proj-[A-Za-z0-9_-]{20,}\b")),
    ("npm_token", re.compile(r"\bnpm_[A-Za-z0-9]{20,}\b")),
    ("google_api_key", re.compile(r"\bAIza[0-9A-Za-z\-_]{20,}\b")),
    ("stripe_live", re.compile(r"\bsk_live_[A-Za-z0-9]{16,}\b")),
    ("bearer_long", re.compile(
        r"(?i)authorization\s*[:=]\s*['\"]?bearer\s+[A-Za-z0-9\-._~+/]{32,}={0,2}"
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


def _range_spec(base: str, head: str) -> str:
    """Three-dot range: merge-base(base, head)..head — matches review_scope diffs."""
    return f"{base}...{head}"


def run_gitleaks(repo: Path, base: str, head: str) -> tuple[int, str]:
    bin_path = shutil.which("gitleaks")
    if not bin_path:
        return -1, ""
    # Align with regex path: three-dot (merge-base) range, not two-dot base..head
    r = subprocess.run(
        [bin_path, "git", f"--log-opts={_range_spec(base, head)}", "--no-banner", "-v"],
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


def _skip_secret_path(path: str) -> bool:
    """Tests/fixtures may embed synthetic tokens for pattern unit tests."""
    p = path.replace("\\", "/").lower()
    if "/tests/" in f"/{p}" or p.startswith("tests/"):
        return True
    if p.endswith((".md", ".rst", ".txt")) and "changelog" in p:
        return True
    if "fixture" in p or "testdata" in p or "test_data" in p:
        return True
    return False


def scan_added_lines_regex(repo: Path, base: str, head: str) -> list[str]:
    r = _git(repo, "diff", "-U0", _range_spec(base, head))
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
        if path and _skip_secret_path(path):
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
        help="Require gitleaks or trufflehog on PATH (alias of --require-scanner). "
        "Findings always fail closed even without this flag.",
    )
    ap.add_argument(
        "--require-scanner",
        action="store_true",
        help="Fail if neither gitleaks nor trufflehog is installed",
    )
    args = ap.parse_args(argv)
    repo = args.repo.resolve()
    require_scanner = bool(args.require_scanner or args.strict)
    rng = _range_spec(args.base, args.head)

    # Prefer external scanners
    for name, runner in (("gitleaks", run_gitleaks), ("trufflehog", run_trufflehog)):
        code, out = runner(repo, args.base, args.head)
        if code < 0:
            continue
        if code == 0:
            print(f"✅ {name}: clean ({rng})")
            return 0
        print(f"❌ {name}: findings\n{out[:4000]}", file=sys.stderr)
        return 1  # external scanner findings always fail closed

    if require_scanner:
        print(
            "❌ neither gitleaks nor trufflehog on PATH "
            "(install one or omit --strict / --require-scanner)",
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
    print(f"✅ regex secret scan clean ({rng})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
