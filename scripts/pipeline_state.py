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

try:
    import fcntl
except ImportError:  # pragma: no cover — non-POSIX
    fcntl = None  # type: ignore

# Five ship phases only (see docs/ship-flow.md). Do not invent others.
VALID_PHASES = {"init", "ready_for_review", "approved", "blocked", "shipped"}


def _state_path() -> Path:
    root = Path(__file__).resolve().parent.parent
    return root / ".agents" / "state" / "pipeline.json"


def _lock_path() -> Path:
    return _state_path().parent / ".pipeline.json.lock"


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


# Optional ADSLC identity fields (A5) — preserved across set-phase
IDENTITY_KEYS = ("spec_id", "card_id", "waiver")


def _default_state() -> dict[str, Any]:
    return {
        "phase": "init",
        "score": None,
        "task": None,
        "remediation": [],
        "spec_id": None,
        "card_id": None,
        "waiver": None,
    }


def get() -> dict[str, Any]:
    p = _state_path()
    if not p.exists():
        return _default_state()
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _default_state()
    if not isinstance(data, dict):
        return _default_state()
    phase = data.get("phase")
    if phase not in VALID_PHASES:
        # Corrupt / hand-edited illegal phase → safe default
        data = {**_default_state(), **{k: v for k, v in data.items() if k != "phase"}}
        data["phase"] = "init"
    # Ensure identity keys exist for readers
    for k in IDENTITY_KEYS:
        data.setdefault(k, None)
    return data


def set_phase(
    phase: str,
    score: float | None = None,
    task: str | None = None,
    *,
    spec_id: str | None = None,
    card_id: str | None = None,
    waiver: str | None = None,
) -> None:
    if phase not in VALID_PHASES:
        raise ValueError(f"Invalid phase: {phase}. Valid: {sorted(VALID_PHASES)}")
    path = _state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    # Serialize read-modify-write so concurrent set-phase calls do not drop fields.
    lock_f = None
    try:
        if fcntl is not None:
            lock_f = open(_lock_path(), "a+", encoding="utf-8")
            fcntl.flock(lock_f.fileno(), fcntl.LOCK_EX)
        state = get()
        state["phase"] = phase
        if score is not None:
            state["score"] = score
        if task is not None:
            state["task"] = task
        if spec_id is not None:
            state["spec_id"] = spec_id
        if card_id is not None:
            state["card_id"] = card_id
        if waiver is not None:
            state["waiver"] = waiver
        _atomic_write(path, state)
    finally:
        if lock_f is not None:
            try:
                fcntl.flock(lock_f.fileno(), fcntl.LOCK_UN)
            except OSError:
                pass
            lock_f.close()


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("get")
    sp = sub.add_parser("set-phase")
    sp.add_argument("phase", choices=sorted(VALID_PHASES))
    sp.add_argument("--score", type=float)
    sp.add_argument("--task", type=str)
    sp.add_argument("--spec-id", type=str, dest="spec_id")
    sp.add_argument("--card-id", type=str, dest="card_id")
    sp.add_argument("--waiver", type=str, help="hotfix|chore|docs-only|prose-only")
    args = ap.parse_args()
    if args.cmd == "get":
        print(json.dumps(get(), indent=2))
    else:
        set_phase(
            args.phase,
            args.score,
            args.task,
            spec_id=args.spec_id,
            card_id=args.card_id,
            waiver=args.waiver,
        )
        print(f"✅ phase → {args.phase}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
