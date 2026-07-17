#!/usr/bin/env python3
"""Scans source for hardcoded paths/URLs/credentials. Zero tolerance (with allowlists)."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".agents",
    "logs",
    "vendor",
    ".antigravitycli",
    ".venv",
    "venv",
    ".mypy_cache",
    ".pytest_cache",
    "infra",
    "cache",
    "var",
    # Portable skill markdown often cites external docs URLs
    "skills",
    # Sample configs / fixtures (product-specific paths)
    "examples",
}
SKIP_FILES = {
    "ALL_PRINCIPLES.md",
    "PRODUCTION_GAP_ANALYSIS.md",
    "README.md",
    "CHANGELOG.md",
    "DEPLOYMENT_GUIDE.md",
    "BACKEND_ROADMAP.md",
    "RELEASE_RUNBOOK.md",
    "PR_DRAFT.md",
    "WORKFLOW_DOCUMENTATION.md",
    # Lockfiles always list package registries
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "poetry.lock",
    "Cargo.lock",
}

# Absolute home paths (not ~/ relative)
ABS_HOME = re.compile(r"/home/[a-zA-Z0-9_-]+", re.I)
WIN_HOME = re.compile(r"C:\\\\Users\\\\", re.I)
INLINE_SECRET = re.compile(
    r"(?<![_\w])(password|secret|api_key|token)\s*=\s*['\"][^'\"]{6,}['\"]",
    re.I,
)
# Placeholders in docs / examples are not real secrets
INLINE_SECRET_PLACEHOLDER = re.compile(
    r"(your-?key|changeme|xxx+|placeholder|example|dummy|todo|insert)",
    re.I,
)
EXPOSED_KEY = re.compile(r"\b[A-Z0-9]{16}\b")
# Any http(s) URL — then filtered by allowlist
ANY_URL = re.compile(r"https?://[\w.-]+\.\w{2,}[^\s)\]'\"`]*", re.I)

# Documentation / public project URLs are not secrets
URL_HOST_ALLOW = re.compile(
    r"^https?://("
    r"localhost|127\.0\.0\.1|example\.com|"
    r"(www\.)?github\.com|"
    r"raw\.githubusercontent\.com|"
    r"pols\.dev|"
    r"(www\.)?lucide\.dev|"
    r"pypi\.org|"
    r"docs\.python\.org|"
    r"(www\.)?npmjs\.com|"
    r"registry\.npmjs\.org|"
    r"fonts\.google\.com|"
    r"fontshare\.com|"
    r"api\.telegram\.org|"
    r"(www\.)?googleapis\.com|"
    r"oauth2\.googleapis\.com|"
    r"accounts\.google\.com|"
    r"console\.cloud\.google\.com|"
    r"api\.openai\.com|"
    r"api\.wise\.com|"
    r"[\w.-]+\.apihub\.citi\.com|"
    r"sandbox\.apihub\.citi\.com"
    r")([/:?]|$)",
    re.I,
)

# Host-bound deploy units and tests may contain machine paths
ALLOW_PREFIXES = (
    "config/settings.py",
    "tests/",
    "test_",
    "conftest.py",
    "migration/deploy/",
    "deploy/",
    "docs/",  # operator manuals may show clone URLs and path examples
    "INSTALL.md",
    "USAGE.md",
    "CONTRIBUTING.md",
)


def _allowed_rel(rel: str) -> bool:
    return any(a in rel for a in ALLOW_PREFIXES)


def main() -> int:
    hits = 0
    for p in ROOT.rglob("*"):
        if not p.is_file():
            continue
        if any(s in p.parts for s in SKIP_DIRS):
            continue
        if p.name in SKIP_FILES:
            continue
        if p.suffix not in {".py", ".md", ".json", ".yaml", ".yml", ".toml"}:
            continue
        # Never scan local OAuth / credential dumps (should be gitignored)
        if p.name in {
            "token.json",
            "credentials.json",
            "client_secret.json",
        } or p.name.startswith("google-credentials"):
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        rel = str(p.relative_to(ROOT)).replace("\\", "/")
        if _allowed_rel(rel):
            continue

        for m in ABS_HOME.finditer(text):
            line = text[: m.start()].count("\n") + 1
            print(f"❌ {rel}:{line} [absolute_user_path] {m.group(0)[:60]}")
            hits += 1
        for m in WIN_HOME.finditer(text):
            line = text[: m.start()].count("\n") + 1
            print(f"❌ {rel}:{line} [windows_user_path] {m.group(0)[:60]}")
            hits += 1
        for m in INLINE_SECRET.finditer(text):
            if INLINE_SECRET_PLACEHOLDER.search(m.group(0)):
                continue
            line = text[: m.start()].count("\n") + 1
            print(f"❌ {rel}:{line} [inline_secret] {m.group(0)[:60]}")
            hits += 1
        for m in ANY_URL.finditer(text):
            url = m.group(0)
            if URL_HOST_ALLOW.search(url):
                continue
            line = text[: m.start()].count("\n") + 1
            print(f"❌ {rel}:{line} [external_url] {url[:60]}")
            hits += 1
        for m in EXPOSED_KEY.finditer(text):
            # digit-only 16-char often false positive; require a letter
            if not re.search(r"[A-Z]", m.group(0)):
                continue
            # Env var names are not keys (e.g. PYTHONUNBUFFERED)
            if m.group(0).isalpha() and m.group(0).isupper() and "_" not in m.group(0):
                # still could be a key; skip known long env-style tokens
                if m.group(0) in {
                    "PYTHONUNBUFFERED",
                    "GOOGLE_APPLICATION_CREDENTIALS",
                }:
                    continue
            if m.group(0) == "PYTHONUNBUFFERED":
                continue
            line = text[: m.start()].count("\n") + 1
            print(f"❌ {rel}:{line} [exposed_api_key] {m.group(0)[:60]}")
            hits += 1

    if hits:
        print(f"❌ {hits} hardcode violation(s)")
        return 1
    print("✅ no hardcodes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
