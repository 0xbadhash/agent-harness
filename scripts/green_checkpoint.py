#!/usr/bin/env python3
"""Bind a green ship (smoke + hard_gates/score) to an exact git SHA.

After score ≥95, write `.agents/state/green_checkpoint.json`.
`next_skill` must not route extra polish (qa_campaign / another review)
while HEAD still equals that SHA.

  python3 scripts/green_checkpoint.py write --score 100
  python3 scripts/green_checkpoint.py check
"""
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path


def _sha(root: Path) -> str:
    r = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(root),
        capture_output=True,
        text=True,
        check=False,
    )
    return (r.stdout or "").strip()


def _dirty(root: Path) -> bool:
    r = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=str(root),
        capture_output=True,
        text=True,
        check=False,
    )
    return bool((r.stdout or "").strip())


def path_for(root: Path) -> Path:
    return root / ".agents" / "state" / "green_checkpoint.json"


def read(root: Path) -> dict:
    p = path_for(root)
    if not p.is_file():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def write(root: Path, *, score: float, sha: str | None = None) -> Path:
    root = root.resolve()
    sha = sha or _sha(root)
    p = path_for(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "sha": sha,
        "score": float(score),
        "updated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%MZ"),
    }
    p.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return p


def head_is_green(root: Path, *, min_score: float = 95.0) -> tuple[bool, str]:
    """True when checkpoint SHA matches HEAD and score ≥ min."""
    data = read(root)
    sha = _sha(root)
    got = str(data.get("sha") or "")
    try:
        score = float(data.get("score") or 0)
    except (TypeError, ValueError):
        score = 0.0
    if not got:
        return False, "no green_checkpoint"
    if got != sha:
        return False, f"checkpoint {got[:12]} != HEAD {sha[:12]}"
    if score < min_score:
        return False, f"checkpoint score {score} < {min_score}"
    if _dirty(root):
        return False, "working tree dirty — green checkpoint does not skip review"
    return True, f"ok: HEAD {sha[:12]} green score={score}"


def extra_loop_forbidden(root: Path) -> tuple[bool, str]:
    """If HEAD is already green, extra polish loops are forbidden."""
    ok, msg = head_is_green(root)
    if ok:
        return True, "forbid extra loop: " + msg
    return False, msg


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path("."))
    sub = ap.add_subparsers(dest="cmd", required=True)
    w = sub.add_parser("write")
    w.add_argument("--score", type=float, required=True)
    sub.add_parser("check")
    args = ap.parse_args(argv)
    root = args.root.resolve()
    if args.cmd == "write":
        p = write(root, score=args.score)
        print(f"green_checkpoint wrote {p} sha={_sha(root)[:12]} score={args.score}")
        return 0
    ok, msg = head_is_green(root)
    print(("✅ " if ok else "· ") + msg)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
