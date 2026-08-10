#!/usr/bin/env python3
"""Atomic FSM state manager. Never hand-edit .agents/state/pipeline.json.

HSQ-2: legal transitions enforced (ship-flow edges). Escape hatch:
``set_phase(..., force_transition=True)`` or CLI ``--force-transition``
(logs to .agents/artifacts/FORCE_TRANSITION_LOG.jsonl).
"""
from __future__ import annotations

import argparse
import json
import sys
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import fcntl
except ImportError:  # pragma: no cover — non-POSIX
    fcntl = None  # type: ignore

# Five ship phases only (see docs/ship-flow.md). Do not invent others.
VALID_PHASES = {"init", "ready_for_review", "approved", "blocked", "shipped"}

# Legal edges from docs/ship-flow.md + self (idempotent) + score re-entry paths.
# Explicitly forbids e.g. init→shipped without --force-transition.
ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    # init→approved/blocked: allow score without prior set-phase ready_for_review
    # (execute_dev often leaves phase at init until pr_validator stamps).
    "init": frozenset({"init", "ready_for_review", "blocked", "approved"}),
    "ready_for_review": frozenset({"ready_for_review", "approved", "blocked", "init"}),
    "approved": frozenset({"approved", "shipped", "blocked", "ready_for_review"}),
    "blocked": frozenset({"blocked", "ready_for_review", "init", "approved"}),
    "shipped": frozenset({"shipped", "init"}),
}


def _state_path() -> Path:
    root = Path(__file__).resolve().parent.parent
    return root / ".agents" / "state" / "pipeline.json"


def _lock_path() -> Path:
    return _state_path().parent / ".pipeline.json.lock"


def _root() -> Path:
    return Path(__file__).resolve().parent.parent


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


def _log_force_transition(from_phase: str, to_phase: str, reason: str) -> None:
    art = _root() / ".agents" / "artifacts"
    try:
        art.mkdir(parents=True, exist_ok=True)
        log = art / "FORCE_TRANSITION_LOG.jsonl"
        row = {
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "from": from_phase,
            "to": to_phase,
            "reason": reason or "unspecified",
            "actor": os.environ.get("USER") or os.environ.get("LOGNAME") or "unknown",
        }
        with log.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except OSError:
        pass


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


def assert_transition_allowed(
    from_phase: str,
    to_phase: str,
    *,
    force: bool = False,
) -> None:
    """Raise ValueError if transition is illegal and force is False."""
    if to_phase not in VALID_PHASES:
        raise ValueError(f"Invalid phase: {to_phase}. Valid: {sorted(VALID_PHASES)}")
    if from_phase not in VALID_PHASES:
        from_phase = "init"
    if force:
        return
    allowed = ALLOWED_TRANSITIONS.get(from_phase, frozenset())
    if to_phase not in allowed:
        raise ValueError(
            f"Illegal FSM transition {from_phase!r} → {to_phase!r}. "
            f"Allowed from {from_phase!r}: {sorted(allowed)}. "
            f"Use --force-transition only with a logged reason."
        )


def set_phase(
    phase: str,
    score: float | None = None,
    task: str | None = None,
    *,
    spec_id: str | None = None,
    card_id: str | None = None,
    waiver: str | None = None,
    force_transition: bool = False,
    force_reason: str = "",
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
        prev = str(state.get("phase") or "init")
        assert_transition_allowed(prev, phase, force=force_transition)
        if force_transition and prev != phase:
            _log_force_transition(prev, phase, force_reason)
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
    sp.add_argument(
        "--force-transition",
        action="store_true",
        help="Allow illegal phase jumps (logged to FORCE_TRANSITION_LOG.jsonl)",
    )
    sp.add_argument(
        "--force-reason",
        default="",
        help="Required in spirit when forcing; stored in force log",
    )
    args = ap.parse_args()
    if args.cmd == "get":
        print(json.dumps(get(), indent=2))
    else:
        try:
            set_phase(
                args.phase,
                args.score,
                args.task,
                spec_id=args.spec_id,
                card_id=args.card_id,
                waiver=args.waiver,
                force_transition=bool(args.force_transition),
                force_reason=str(args.force_reason or ""),
            )
        except ValueError as e:
            print(f"❌ {e}", file=sys.stderr)
            return 1
        print(f"✅ phase → {args.phase}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
