#!/usr/bin/env python3
"""Atomic FSM state manager. Never hand-edit .agents/state/pipeline.json."""
from __future__ import annotations

import argparse
import json
import sys
import os
import tempfile
from pathlib import Path
from typing import Any

VALID_PHASES = {"init", "ready_for_review", "approved", "blocked", "shipped", "missing"}

def _state_path() -> Path:
    root = Path(__file__).resolve().parent.parent
    return root / ".agents" / "state" / "pipeline.json"

def _atomic_write(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, sort_keys=True)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)  # atomic on POSIX + Windows (Python 3.3+)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def get() -> dict[str, Any]:
    p = _state_path()
    if not p.exists():
        return {"phase": "init", "score": None, "task": None, "remediation": []}
    return json.loads(p.read_text(encoding="utf-8"))

def set_phase(phase: str, score: float | None = None, task: str | None = None) -> None:
    if phase not in VALID_PHASES:
        raise ValueError(f"Invalid phase: {phase}. Valid: {VALID_PHASES}")
    state = get()
    state["phase"] = phase
    if score is not None:
        state["score"] = score
    if task is not None:
        state["task"] = task
    _atomic_write(_state_path(), state)

def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("get")
    sp = sub.add_parser("set-phase")
    sp.add_argument("phase", choices=sorted(VALID_PHASES))
    sp.add_argument("--score", type=float)
    sp.add_argument("--task", type=str)
    args = ap.parse_args()
    if args.cmd == "get":
        print(json.dumps(get(), indent=2))
    else:
        set_phase(args.phase, args.score, args.task)
        print(f"✅ phase → {args.phase}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
