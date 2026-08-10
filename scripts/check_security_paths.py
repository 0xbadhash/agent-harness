#!/usr/bin/env python3
"""G8 — if diff touches product_plugin security_paths, require security test mention."""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


def _load_security_paths(root: Path) -> list[str]:
    plugin = root / ".agents" / "product_plugin.yaml"
    if not plugin.is_file():
        plugin = root / "product_plugin.yaml"
    if not plugin.is_file():
        return []
    text = plugin.read_text(encoding="utf-8", errors="replace")
    # minimal parse: security_paths: list
    paths: list[str] = []
    in_block = False
    for line in text.splitlines():
        if re.match(r"^\s*security_paths\s*:", line):
            in_block = True
            # inline list?
            rest = line.split(":", 1)[1].strip()
            if rest.startswith("["):
                for m in re.finditer(r"['\"]([^'\"]+)['\"]", rest):
                    paths.append(m.group(1))
                in_block = False
            continue
        if in_block:
            if re.match(r"^\S", line) and not line.strip().startswith("-"):
                break
            m = re.match(r"^\s*-\s*['\"]?([^'\"#]+)", line)
            if m:
                paths.append(m.group(1).strip())
            elif line.strip() and not line.strip().startswith("#"):
                if not line.strip().startswith("-"):
                    break
    return [p.strip().strip("/") for p in paths if p.strip()]


def _changed(repo: Path, base: str, head: str) -> list[str]:
    for sep in ("...", ".."):
        r = subprocess.run(
            ["git", "diff", "--name-only", "--diff-filter=ACMR", f"{base}{sep}{head}"],
            cwd=str(repo),
            capture_output=True,
            text=True,
            check=False,
        )
        if r.returncode == 0:
            return [ln.strip().replace("\\", "/") for ln in (r.stdout or "").splitlines() if ln.strip()]
    return []


def check(repo: Path, base: str, head: str) -> tuple[bool, list[str]]:
    repo = repo.resolve()
    spaths = _load_security_paths(repo)
    if not spaths:
        return True, ["ok: no security_paths configured"]
    changed = _changed(repo, base, head)
    hits = []
    for c in changed:
        for s in spaths:
            if c == s or c.startswith(s.rstrip("/") + "/") or f"/{s}/" in f"/{c}/":
                hits.append(c)
                break
    if not hits:
        return True, ["ok: security_paths not in diff"]

    # require tests mentioning security/authz/threat or path stem
    corpus = []
    for base_d in (repo / "tests",):
        if base_d.is_dir():
            for p in base_d.rglob("test_*.py"):
                try:
                    corpus.append(p.read_text(encoding="utf-8", errors="replace"))
                except OSError:
                    pass
    blob = "\n".join(corpus).lower()
    if not any(
        k in blob
        for k in ("security", "authz", "authn", "threat", "idor", "ssrf", "injection")
    ):
        # also accept stem of hit file
        for h in hits:
            stem = Path(h).stem.lower()
            if stem and stem in blob:
                return True, [f"ok: security path tests via stem ({stem})"]
        return False, [
            f"security_paths touched ({hits[:5]}) but no security-oriented tests found — "
            "add tests/test_* mentioning security/authz or path stem"
        ]
    return True, [f"ok: security_paths {hits[:5]} covered by security tests"]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", type=Path, default=Path("."))
    ap.add_argument("--base", default="HEAD~1")
    ap.add_argument("--head", default="HEAD")
    args = ap.parse_args(argv)
    ok, msgs = check(args.repo.resolve(), args.base, args.head)
    for m in msgs:
        print(("✅ " if ok else "❌ ") + m)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
