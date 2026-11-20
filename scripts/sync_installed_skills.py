#!/usr/bin/env python3
"""Copy skills/<name>/ onto .agents/skills/<name>/.

Does not delete an install directory that skills/ lacks unless
``--delete-listed <name>`` names it. File copies inside a skill that
exists on both sides replace bytes and drop install-only files in that
skill so the drift check can go green.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


def _skill_dirs(path: Path) -> list[Path]:
    if not path.is_dir():
        return []
    return sorted(p for p in path.iterdir() if p.is_dir())


def _copy_skill(src: Path, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    copied: set[str] = set()
    for path in src.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(src).as_posix()
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(path.read_bytes())
        copied.add(rel)
    for path in list(dest.rglob("*")):
        if path.is_file() and path.relative_to(dest).as_posix() not in copied:
            path.unlink()


def sync(root: Path, delete_listed: list[str]) -> int:
    skills = root / "skills"
    install = root / ".agents" / "skills"
    if not skills.is_dir():
        print(f"skills/ missing under {root}", file=sys.stderr)
        return 1
    install.mkdir(parents=True, exist_ok=True)
    source_names = {p.name for p in _skill_dirs(skills)}
    for src in _skill_dirs(skills):
        _copy_skill(src, install / src.name)
        print(f"synced {src.name}")
    listed = set(delete_listed)
    for name in sorted(listed):
        if name in source_names:
            print(f"refuse delete {name}: present in skills/", file=sys.stderr)
            return 1
        extra = install / name
        if extra.is_dir():
            shutil.rmtree(extra)
            print(f"deleted listed {name}")
        else:
            print(f"delete-listed {name}: not present")
    for dest in _skill_dirs(install):
        if dest.name not in source_names:
            print(
                f"keep extra {dest.name}: pass --delete-listed {dest.name} to remove"
            )
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument(
        "--delete-listed",
        action="append",
        default=[],
        help="Install directory name to remove. Refused when skills/ has that name.",
    )
    args = ap.parse_args(argv)
    return sync(args.root.expanduser().resolve(), args.delete_listed)


if __name__ == "__main__":
    sys.exit(main())
