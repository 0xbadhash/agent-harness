#!/usr/bin/env python3
"""Check that a prototype informed the spec and never became the implementation.

Rules (E22/E23):

- ``**Prototype:** none`` skips the check.
- A named prototype must carry ``**Prototype verdict:**`` that selects a variant
  or records that the directory was deleted.
- Every ``variant-*.md`` still present must say ``DO NOT SHIP``.
- A prototype path may not point into an implementation directory.
- Source files may not contain the prototype header or marker.

Usage::

  python3 scripts/check_prototype_fidelity.py --root .
  python3 scripts/check_prototype_fidelity.py --root . --spec <path>
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

PROTO_RE = re.compile(r"\*\*Prototype:\*\*\s*(.+)", re.IGNORECASE)
VERDICT_RE = re.compile(r"\*\*Prototype verdict:\*\*\s*(.+)", re.IGNORECASE)
HEADER_RE = re.compile(r"^#\s+Prototype\s+\S+\s+—\s+variant\s+[abc]\b", re.MULTILINE)
MARKER = "DO NOT SHIP"
SOURCE_DIRS = ("scripts", "src", "app", "lib", "bin", "skills")
SOURCE_SUFFIXES = {".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".sh", ".php"}


def _read(path: Path | None) -> str:
    if path is None or not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _spec_path(root: Path, spec: Path | None) -> Path | None:
    if spec is not None:
        return spec if spec.is_absolute() else root / spec
    pipeline = root / ".agents" / "state" / "pipeline.json"
    if pipeline.is_file():
        import json

        try:
            data = json.loads(pipeline.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        rel = str(data.get("spec_id") or "")
        if rel and (root / rel).is_file():
            return root / rel
    return None


def _clean(value: str) -> str:
    return value.strip().strip("`").strip()


def check(root: Path, *, spec: Path | None = None) -> tuple[bool, list[str]]:
    """Return (ok, messages) for the prototype contract."""
    root = Path(root)
    text = _read(_spec_path(root, spec)) + "\n" + _read(root / "PR_DRAFT.md")
    proto_match = PROTO_RE.search(text)
    if proto_match is None:
        return True, ["ok: no **Prototype:** field — fidelity check N/A"]
    value = _clean(proto_match.group(1))
    if value.lower() in {"none", "n/a", "na", "-", "not-applicable"}:
        return True, ["ok: prototype not used"]

    failures: list[str] = []
    resolved = Path(value)
    if not resolved.is_absolute():
        resolved = root / resolved
    if "prototypes" not in resolved.parts:
        failures.append(
            f"**Prototype:** {value!r} must live under .agents/prototypes/; "
            "implementation directories are not prototypes"
        )

    verdict_match = VERDICT_RE.search(text)
    verdict = _clean(verdict_match.group(1)) if verdict_match else ""
    if not verdict or verdict.lower() in {"none", "n/a", "na", "-"}:
        failures.append(
            "missing **Prototype verdict:** — record the chosen variant and why, "
            "or that the prototype directory was deleted"
        )
    elif resolved.is_dir() and not re.search(r"\b(variant\s+[abc]|deleted|rejected)\b", verdict, re.I):
        failures.append(
            "**Prototype verdict:** must name variant a/b/c, or say deleted/rejected"
        )
    elif not resolved.is_dir() and "delet" not in verdict.lower():
        failures.append(
            f"prototype directory {resolved} is gone; the verdict must say it was deleted"
        )

    if resolved.is_dir():
        variants = sorted(resolved.glob("variant-*.md"))
        if not variants:
            failures.append(f"{resolved} has no variant-*.md files")
        for variant in variants:
            body = _read(variant)
            if MARKER not in body:
                failures.append(f"{variant.relative_to(root)} is missing 'DO NOT SHIP'")

    for area in SOURCE_DIRS:
        base = root / area
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in SOURCE_SUFFIXES:
                continue
            body = _read(path)
            if HEADER_RE.search(body) or MARKER in body:
                failures.append(
                    f"{path.relative_to(root)} contains prototype code — copy the "
                    "shape, not the sketch"
                )

    if failures:
        return False, failures
    return True, [f"ok: prototype {value!r} recorded and contained"]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--spec", type=Path, default=None)
    args = ap.parse_args(argv)
    ok, msgs = check(args.root, spec=args.spec)
    for msg in msgs:
        print(("✅ " if ok else "❌ ") + msg)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
