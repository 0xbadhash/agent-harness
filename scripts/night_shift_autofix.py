#!/usr/bin/env python3
"""Bounded auto-fix helpers for night_shift readiness (ORCH-P3).

**Allowed:** mechanical fixes that restore readiness (deps, formatters, lockfile install).
**Forbidden:** inventing product features, release/tag/push, broad refactors, secret changes.

Used by ``night_shift_readiness.py`` after a failed gate pass; re-run gates once.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


def _run(
    cmd: list[str],
    *,
    cwd: Path,
    timeout: int = 900,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    try:
        r = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env or os.environ.copy(),
            check=False,
        )
        return {
            "cmd": cmd,
            "exit": r.returncode,
            "ok": r.returncode == 0,
            "stdout_tail": (r.stdout or "")[-1200:],
            "stderr_tail": (r.stderr or "")[-600:],
        }
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "cmd": cmd,
            "exit": 124,
            "ok": False,
            "stdout_tail": "",
            "stderr_tail": str(exc),
        }


def _venv_python(root: Path) -> str:
    for rel in (".venv/bin/python", "venv/bin/python", ".venv/bin/python3", "venv/bin/python3"):
        p = root / rel
        if p.is_file() and os.access(p, os.X_OK):
            return str(p)
    return sys.executable


def _combined_tails(results: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for r in results:
        if r.get("ok"):
            continue
        parts.append(r.get("stdout_tail") or "")
        parts.append(r.get("stderr_tail") or "")
        parts.append(r.get("name") or "")
    return "\n".join(parts)


def try_ensure_dev_env(root: Path, *, dry_run: bool) -> dict[str, Any] | None:
    """Install product venv / requirements-dev when gates fail on missing deps."""
    scripts = root / "scripts"
    ensure = scripts / "ensure_product_dev_env.py"
    harness_ensure = Path(__file__).resolve().parent / "ensure_product_dev_env.py"
    target = ensure if ensure.is_file() else harness_ensure
    if not target.is_file():
        # inline minimal: requirements-dev + venv
        req = root / "requirements-dev.txt"
        if not req.is_file():
            return None
        py = _venv_python(root)
        if dry_run:
            return {
                "name": "ensure_dev_env",
                "ok": True,
                "dry_run": True,
                "detail": f"would pip install -r {req} with {py}",
            }
        venv = root / ".venv"
        if not (venv / "bin" / "python").is_file():
            _run([sys.executable, "-m", "venv", str(venv)], cwd=root, timeout=120)
            py = str(venv / "bin" / "python")
        r = _run([py, "-m", "pip", "install", "-r", str(req)], cwd=root, timeout=1200)
        r["name"] = "ensure_dev_env"
        r["detail"] = "pip install -r requirements-dev.txt"
        return r

    py = sys.executable
    if dry_run:
        return {
            "name": "ensure_dev_env",
            "ok": True,
            "dry_run": True,
            "detail": f"would run {target}",
        }
    # ensure_product_dev_env may be importable
    if target.name == "ensure_product_dev_env.py":
        sys.path.insert(0, str(target.parent))
        try:
            from ensure_product_dev_env import ensure_product_dev_env  # type: ignore

            out = ensure_product_dev_env(root, dry_run=False)
            return {
                "name": "ensure_dev_env",
                "ok": bool(out.get("ok")),
                "exit": 0 if out.get("ok") else 1,
                "detail": str(out.get("message") or out.get("status") or out),
                "stdout_tail": str(out)[:800],
                "stderr_tail": "",
            }
        except Exception as exc:  # noqa: BLE001
            r = _run([py, str(target), str(root)], cwd=root, timeout=1200)
            r["name"] = "ensure_dev_env"
            r["detail"] = f"script fallback after import err: {exc}"
            return r
    r = _run([py, str(target)], cwd=root, timeout=1200)
    r["name"] = "ensure_dev_env"
    return r


def try_npm_ci(root: Path, *, dry_run: bool) -> dict[str, Any] | None:
    if not (root / "package.json").is_file():
        return None
    if dry_run:
        return {
            "name": "npm_install",
            "ok": True,
            "dry_run": True,
            "detail": "would npm ci || npm install",
        }
    if (root / "package-lock.json").is_file():
        r = _run(["npm", "ci"], cwd=root, timeout=1200)
        if r["ok"]:
            r["name"] = "npm_install"
            r["detail"] = "npm ci"
            return r
    r = _run(["npm", "install"], cwd=root, timeout=1200)
    r["name"] = "npm_install"
    r["detail"] = "npm install"
    return r


def try_ruff_fix(root: Path, *, dry_run: bool) -> dict[str, Any] | None:
    py = _venv_python(root)
    # ruff check --fix on scripts/ and tests/ only (bounded)
    targets = [p for p in ("scripts", "tests", "src") if (root / p).is_dir()]
    if not targets:
        return None
    cmd = [py, "-m", "ruff", "check", "--fix", *targets]
    if dry_run:
        return {
            "name": "ruff_fix",
            "ok": True,
            "dry_run": True,
            "detail": " ".join(cmd),
        }
    r = _run(cmd, cwd=root, timeout=300)
    if r["exit"] == 127 or "No module named ruff" in (r.get("stderr_tail") or ""):
        return None
    r["name"] = "ruff_fix"
    r["detail"] = "ruff check --fix (scripts/tests/src)"
    return r


def try_black_format(root: Path, *, dry_run: bool) -> dict[str, Any] | None:
    py = _venv_python(root)
    targets = [p for p in ("scripts", "tests") if (root / p).is_dir()]
    if not targets:
        return None
    cmd = [py, "-m", "black", *targets]
    if dry_run:
        return {
            "name": "black_format",
            "ok": True,
            "dry_run": True,
            "detail": " ".join(cmd),
        }
    r = _run(cmd, cwd=root, timeout=300)
    if r["exit"] == 127 or "No module named black" in (r.get("stderr_tail") or ""):
        return None
    r["name"] = "black_format"
    r["detail"] = "black scripts/ tests/"
    return r


def try_trailing_whitespace(root: Path, *, dry_run: bool) -> dict[str, Any] | None:
    """Strip trailing whitespace on recently modified text files under scripts/ (bounded)."""
    scripts = root / "scripts"
    if not scripts.is_dir():
        return None
    changed = 0
    files: list[Path] = []
    for p in scripts.rglob("*.py"):
        if p.name.startswith("."):
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except OSError:
            continue
        lines = text.splitlines(keepends=True)
        new_lines = [re.sub(r"[ \t]+(\r?\n)", r"\1", ln) for ln in lines]
        new = "".join(new_lines)
        if new != text:
            files.append(p)
            if not dry_run:
                p.write_text(new, encoding="utf-8")
            changed += 1
    if not changed:
        return None
    return {
        "name": "trailing_whitespace",
        "ok": True,
        "exit": 0,
        "dry_run": dry_run,
        "detail": f"{'would strip' if dry_run else 'stripped'} trailing ws in {changed} script(s)",
        "stdout_tail": "\n".join(str(f.relative_to(root)) for f in files[:20]),
        "stderr_tail": "",
    }


def attempt_autofix(
    root: Path,
    results: list[dict[str, Any]],
    *,
    dry_run: bool = False,
    product_id: str = "",
) -> list[dict[str, Any]]:
    """Run bounded fixers relevant to failed gates. Returns list of attempt records."""
    failed = [r for r in results if not r.get("ok")]
    if not failed:
        return []

    names = {r.get("name") for r in failed}
    tails = _combined_tails(results).lower()
    attempts: list[dict[str, Any]] = []

    need_deps = bool(
        names & {"validate_full", "product_smoke", "coverage", "security_pytest"}
    ) or any(
        k in tails
        for k in (
            "modulenotfounderror",
            "no module named",
            "cannot find module",
            "err_module_not_found",
            "cannot find package",
        )
    )
    if need_deps:
        a = try_ensure_dev_env(root, dry_run=dry_run)
        if a:
            attempts.append(a)

    if "product_smoke" in names or "validate_full" in names:
        if (root / "package.json").is_file() and any(
            k in tails
            for k in (
                "cannot find module",
                "err_module_not_found",
                "npm err",
                "enoent",
                "node_modules",
            )
        ):
            a = try_npm_ci(root, dry_run=dry_run)
            if a:
                attempts.append(a)

    if names & {"repo_hygiene", "validate_full", "hardcodes"}:
        a = try_ruff_fix(root, dry_run=dry_run)
        if a:
            attempts.append(a)
        a = try_black_format(root, dry_run=dry_run)
        if a:
            attempts.append(a)
        a = try_trailing_whitespace(root, dry_run=dry_run)
        if a:
            attempts.append(a)

    # Annotate product id for logs
    for a in attempts:
        a["product_id"] = product_id
    return attempts


def propose_roadmap_items(
    root: Path,
    results: list[dict[str, Any]],
    matrix_missing: list[str],
    product_id: str,
) -> list[str]:
    """Evidence-based roadmap *proposals* only — never invent greenfield features.

    Each item cites a gate tail, matrix gap, or explicit PRD open checkbox.
    """
    proposals: list[str] = []
    failed = [r for r in results if not r.get("ok")]

    # Matrix gaps → propose restoring or retiring the surface (evidence: missing paths)
    for miss in matrix_missing[:8]:
        proposals.append(
            f"[{product_id}] PROPOSE roadmap: restore or retire test surface "
            f"`{miss}` (evidence: TEST_MATRIX missing path)."
        )

    for r in failed:
        name = r.get("name") or ""
        tail = ((r.get("stderr_tail") or "") + "\n" + (r.get("stdout_tail") or ""))[
            :400
        ]
        if name == "product_smoke":
            proposals.append(
                f"[{product_id}] PROPOSE roadmap: repair or rewrite product_plugin "
                f"smoke[] steps (evidence: product_smoke exit {r.get('exit')})."
            )
        elif name == "coverage":
            proposals.append(
                f"[{product_id}] PROPOSE roadmap: raise coverage on failing modules "
                f"or adjust config/coverage_config.json fail_under "
                f"(evidence: coverage gate)."
            )
        elif name.startswith("security"):
            proposals.append(
                f"[{product_id}] PROPOSE roadmap (P0): security gate remediation "
                f"`{name}` before feature work (evidence: security failure)."
            )
        elif name.startswith("live_http") or name == "static_denies_live":
            proposals.append(
                f"[{product_id}] PROPOSE ops ticket: live probe `{name}` "
                f"(evidence: HTTP/nginx deny failure) — not a product feature invent."
            )
        elif name == "hardcodes" and "secret" in tail.lower():
            proposals.append(
                f"[{product_id}] PROPOSE roadmap (P0): secret/hardcode cleanup "
                f"(evidence: hardcodes gate)."
            )

    # Explicit open AC in product roadmap / PRD (not invented)
    for rel in ("memory/PRD.md", ".agents/BACKLOG.md", "docs/ROADMAP.md", "ROADMAP.md"):
        path = root / rel
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        opens = re.findall(r"^\s*- \[ \] (.+)$", text, re.M)
        for item in opens[:5]:
            item = item.strip()
            if len(item) < 8:
                continue
            proposals.append(
                f"[{product_id}] PROPOSE roadmap (existing open AC): {item[:120]} "
                f"(evidence: unchecked box in {rel})."
            )

    # Dedupe preserve order
    seen: set[str] = set()
    out: list[str] = []
    for p in proposals:
        if p in seen:
            continue
        seen.add(p)
        out.append(p)
    return out[:12]
