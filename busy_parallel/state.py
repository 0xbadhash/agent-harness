"""Tiny JSON state for dedupe, caps, and the kill switch. Stdlib only."""

from __future__ import annotations

import json
import time
from pathlib import Path


def state_dir(home: Path) -> Path:
    path = home / "state" / "busy-parallel"
    path.mkdir(parents=True, exist_ok=True)
    return path


def enabled(home: Path) -> bool:
    root = state_dir(home)
    if (root / "DISABLED").exists():
        return False
    return (root / "ENABLE").is_file()


def _load(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def _save(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data), encoding="utf-8")
    tmp.replace(path)


def seen(home: Path, message_id: str) -> bool:
    return message_id in set(_load(state_dir(home) / "seen.json", []))


def mark_seen(home: Path, message_id: str) -> None:
    path = state_dir(home) / "seen.json"
    ids = list(_load(path, []))
    if message_id not in ids:
        ids.append(message_id)
    _save(path, ids[-500:])


def inflight(home: Path) -> list:
    now = time.time()
    rows = [r for r in _load(state_dir(home) / "inflight.json", []) if now - float(r.get("ts", 0)) < 3600]
    _save(state_dir(home) / "inflight.json", rows)
    return rows


def add_inflight(home: Path, job_id: str) -> None:
    rows = inflight(home)
    rows.append({"job_id": job_id, "ts": time.time()})
    _save(state_dir(home) / "inflight.json", rows)


def recent_launches(home: Path, window: float = 60.0) -> int:
    now = time.time()
    path = state_dir(home) / "rate.json"
    stamps = [t for t in _load(path, []) if now - float(t) < window]
    _save(path, stamps)
    return len(stamps)


def mark_launch(home: Path) -> None:
    path = state_dir(home) / "rate.json"
    stamps = [t for t in _load(path, []) if time.time() - float(t) < 60]
    stamps.append(time.time())
    _save(path, stamps)
