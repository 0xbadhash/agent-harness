#!/usr/bin/env python3
"""Ensure a product checkout has a usable Python env for night_shift gates.

Policy (report-only readiness; this helper may create .venv + pip install):
  - Prefer product .venv
  - If requirements-dev.txt exists and pytest (etc.) missing → create venv + pip install
  - Never sudo pip / never write system site-packages
  - No product source auto-fix

Used by bin/night_shift_all_products.py preflight.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any

REQUIRED_IMPORTS = ("pytest",)


def _venv_python(root: Path) -> Path | None:
    for rel in (".venv/bin/python", "venv/bin/python", ".venv/bin/python3", "venv/bin/python3"):
        p = root / rel
        if p.is_file() and os.access(p, os.X_OK):
            return p
    return None


def _can_import(python: str, names: tuple[str, ...] = REQUIRED_IMPORTS) -> bool:
    code = "import " + ",".join(names)
    try:
        r = subprocess.run(
            [python, "-c", code],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        return r.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def _run(cmd: list[str], *, timeout: int = 600) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def ensure_product_dev_env(
    root: Path,
    *,
    python: str | None = None,
    dry_run: bool = False,
    required: tuple[str, ...] = REQUIRED_IMPORTS,
) -> dict[str, Any]:
    """Return {ok, status, message, python}.

    status: ok | installed | skip | dry-run | fail
    """
    root = root.resolve()
    req = root / "requirements-dev.txt"
    ensure_script = root / "scripts" / "ensure_dev_deps.py"

    vpy = _venv_python(root)
    candidate = str(vpy) if vpy else (python or sys.executable)

    if _can_import(candidate, required):
        # Optional product ensure_dev_deps for extra checks
        if ensure_script.is_file() and not dry_run:
            _run([candidate, str(ensure_script)], timeout=120)
        return {
            "ok": True,
            "status": "ok",
            "message": f"imports ok via {candidate}",
            "python": candidate,
        }

    if not req.is_file():
        return {
            "ok": True,
            "status": "skip",
            "message": "pytest missing and no requirements-dev.txt — skip install",
            "python": candidate,
        }

    if dry_run:
        return {
            "ok": True,
            "status": "dry-run",
            "message": f"would create/update .venv and pip install -r {req.name}",
            "python": candidate,
        }

    venv_dir = root / ".venv"
    venv_py = venv_dir / "bin" / "python"
    try:
        if not venv_py.is_file():
            r = _run([sys.executable, "-m", "venv", str(venv_dir)], timeout=120)
            if r.returncode != 0:
                return {
                    "ok": False,
                    "status": "fail",
                    "message": f"venv create failed: {(r.stderr or r.stdout)[-400:]}",
                    "python": candidate,
                }
        pip = [str(venv_py), "-m", "pip", "install", "-r", str(req)]
        r = _run(pip, timeout=600)
        if r.returncode != 0:
            return {
                "ok": False,
                "status": "fail",
                "message": f"pip install failed: {(r.stderr or r.stdout)[-500:]}",
                "python": str(venv_py),
            }
        if not _can_import(str(venv_py), required):
            return {
                "ok": False,
                "status": "fail",
                "message": f"after install still missing {required}",
                "python": str(venv_py),
            }
        if ensure_script.is_file():
            _run([str(venv_py), str(ensure_script)], timeout=120)
        return {
            "ok": True,
            "status": "installed",
            "message": f"installed {req.name} into {venv_dir}",
            "python": str(venv_py),
        }
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "status": "fail",
            "message": "venv/pip timeout",
            "python": candidate,
        }
    except OSError as exc:
        return {
            "ok": False,
            "status": "fail",
            "message": str(exc),
            "python": candidate,
        }


def main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("root", type=Path, nargs="?", default=Path("."))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    r = ensure_product_dev_env(args.root, dry_run=args.dry_run)
    print(f"{r['status']}: {r['message']} (python={r.get('python')})")
    return 0 if r["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
