#!/usr/bin/env python3
"""Literal import-boundary check. Stdlib ast only.

Flags two cases:
  - a sys.path insert/append whose argument is a string literal outside --root
  - a string literal that contains an absolute /home/<user>/<other-repo>/ path

Does not resolve stdlib or third-party module names. A relative import and a
plain ``import os`` pass. Directories named tests, .venv, and .agents are
skipped: tests hold hardcode-scanner fixtures, not product imports.
"""
from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".agents",
    "node_modules",
    "site-packages",
    "tests",
}
FIX = (
    "FIX: keep sys.path on this repo's scripts/ directory. "
    "Do not point it at another product tree."
)
_OTHER_ROOT = re.compile(r"/home/([^/\s\"']+)/([A-Za-z0-9][A-Za-z0-9_.-]*)/")


def _py_files(root: Path) -> list[Path]:
    found: list[Path] = []
    if not root.is_dir():
        return found
    for dirpath, dirnames, filenames in root.walk() if hasattr(Path, "walk") else _walk(root):
        # Path.walk yields (dir, dirnames, filenames) on 3.12+. _walk matches that.
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.endswith(".egg-info")]
        for name in filenames:
            if name.endswith(".py"):
                found.append(dirpath / name)
    return found


def _walk(root: Path):
    import os

    for dirpath, dirnames, filenames in os.walk(root):
        yield Path(dirpath), dirnames, filenames


def _inside(path_text: str, root: Path) -> bool:
    try:
        candidate = Path(path_text).expanduser().resolve()
        root_res = root.resolve()
    except OSError:
        return False
    return candidate == root_res or root_res in candidate.parents or candidate in root_res.parents


def _is_sys_path_call(node: ast.Call) -> bool:
    func = node.func
    if not isinstance(func, ast.Attribute):
        return False
    if func.attr not in {"insert", "append"}:
        return False
    inner = func.value
    return (
        isinstance(inner, ast.Attribute)
        and inner.attr == "path"
        and isinstance(inner.value, ast.Name)
        and inner.value.id == "sys"
    )


def _path_arg(node: ast.Call) -> ast.expr | None:
    func = node.func
    if isinstance(func, ast.Attribute) and func.attr == "insert":
        return node.args[1] if len(node.args) >= 2 else None
    if node.args:
        return node.args[0]
    return None


def _other_homes(text: str, root: Path) -> list[str]:
    hits: list[str] = []
    root_name = root.resolve().name
    for match in _OTHER_ROOT.finditer(text):
        repo = match.group(2)
        if repo == root_name:
            continue
        literal = match.group(0)
        if _inside(literal, root):
            continue
        hits.append(literal.rstrip("/"))
    return hits


def scan(root: Path) -> list[str]:
    problems: list[str] = []
    root = root.resolve()
    for path in _py_files(root):
        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(path))
        except (OSError, SyntaxError):
            continue
        rel = path.relative_to(root).as_posix()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and _is_sys_path_call(node):
                arg = _path_arg(node)
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    text = arg.value
                    if text.startswith("/") and not _inside(text, root):
                        snippet = text if len(text) <= 80 else text[:77] + "..."
                        problems.append(
                            f"{rel}:{getattr(node, 'lineno', 0)} [import_boundary] {snippet} {FIX}"
                        )
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                for hit in _other_homes(node.value, root):
                    problems.append(
                        f"{rel}:{getattr(node, 'lineno', 0)} [import_boundary] {hit} {FIX}"
                    )
    return problems


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = ap.parse_args(argv)
    root = args.root.expanduser().resolve()
    found = scan(root)
    if found:
        print("\n".join(found))
        return 1
    print("import boundary ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
