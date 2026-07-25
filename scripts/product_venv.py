#!/usr/bin/env python3
"""Locate product virtualenv interpreters without collapsing Unix venv symlinks.

On Linux/macOS, ``.venv/bin/python`` is often a symlink to the base system
interpreter. ``Path.resolve()`` follows that link to e.g. ``/usr/bin/python3``,
which **drops venv site-packages** (``pytest`` missing). Night-shift smoke then
fails with ``No module named pytest`` even when ``.venv`` has pytest installed.

Use an absolute path that still lives under ``.venv`` / ``venv``:
- Windows: prefer ``.venv\\Scripts\\python.exe``
- POSIX: prefer ``.venv/bin/python`` then ``python3``

Shared by ``product_smoke``, ``night_shift_readiness``, and
``night_shift_all_products`` (SoT in agent-harness; installed into products).
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Optional, Sequence


def product_venv_python(product_root: Path) -> Optional[Path]:
    """Return path to product venv interpreter, or None if missing."""
    root = product_root.expanduser()
    if not root.is_absolute():
        root = root.absolute()

    if sys.platform == "win32":
        candidates: List[Path] = [
            Path(".venv") / "Scripts" / "python.exe",
            Path("venv") / "Scripts" / "python.exe",
            Path(".venv") / "bin" / "python.exe",
            Path(".venv") / "bin" / "python",
            Path(".venv") / "bin" / "python3",
        ]
    else:
        candidates = [
            Path(".venv") / "bin" / "python",
            Path(".venv") / "bin" / "python3",
            Path("venv") / "bin" / "python",
            Path("venv") / "bin" / "python3",
            Path(".venv") / "Scripts" / "python.exe",
            Path("venv") / "Scripts" / "python.exe",
        ]

    for rel in candidates:
        cand = root / rel
        try:
            if not cand.is_file():
                continue
        except OSError:
            continue
        # absolute() does not resolve symlinks (unlike resolve()).
        return cand.absolute()
    return None


def rewrite_smoke_python(cmd: Sequence[str], product_root: Path) -> List[str]:
    """Replace bare python/python3/py with product venv interpreter when present."""
    if not cmd or cmd[0] not in ("python", "python3", "py"):
        return list(cmd)
    vpy = product_venv_python(product_root)
    if vpy is None:
        return list(cmd)
    out = list(cmd)
    out[0] = str(vpy)
    return out
