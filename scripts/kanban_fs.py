#!/usr/bin/env python3
"""Shared vault IO for kanban watchers (secondbrain-owned paths).

Centralizes log/state/board writes so modules do not reimplement sudo-tee.
"""
from __future__ import annotations

import fcntl
import json
import os
import subprocess
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


def utc_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@contextmanager
def board_lock(board: Path, *, timeout_sec: float = 30.0) -> Iterator[None]:
    """Exclusive flock for kanban.md read-modify-write (all writers).

    Lock file sits beside the board so lockers do not need write access to
    the markdown itself before acquiring.
    """
    lock_path = board.parent / ".kanban.board.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(lock_path), os.O_CREAT | os.O_RDWR, 0o664)
    try:
        deadline = time.monotonic() + timeout_sec
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise TimeoutError(f"kanban board lock timeout: {lock_path}") from None
                time.sleep(0.05)
        yield
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)


def write_text(path: Path, text: str, *, user: str = "secondbrain") -> None:
    """Prefer vault_fs write-gateway; fall back to direct/sudo tee."""
    try:
        from vault_fs import write_text as _vault_write  # type: ignore
    except ImportError:
        _vault_write = None  # type: ignore
    if _vault_write is not None:
        _vault_write(path, text)
        return
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.write_text(text, encoding="utf-8")
    except OSError:
        r = subprocess.run(
            ["sudo", "-u", user, "tee", str(path)],
            input=text.encode("utf-8"),
            capture_output=True,
            check=False,
        )
        if r.returncode != 0:
            raise PermissionError(r.stderr.decode(errors="replace")) from None


def append_line(path: Path, line: str, *, user: str = "secondbrain") -> None:
    if not line.endswith("\n"):
        line = line + "\n"
    try:
        from vault_fs import append_text as _vault_append  # type: ignore
    except ImportError:
        _vault_append = None  # type: ignore
    if _vault_append is not None:
        _vault_append(path, line)
        return
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("a", encoding="utf-8") as f:
            f.write(line)
    except OSError:
        r = subprocess.run(
            ["sudo", "-u", user, "tee", "-a", str(path)],
            input=line.encode("utf-8"),
            capture_output=True,
            check=False,
        )
        if r.returncode != 0:
            raise PermissionError(r.stderr.decode(errors="replace")) from None


def append_log(vault: Path, name: str, msg: str, *, also_print: bool = True) -> None:
    path = vault / "agent-tasks" / name
    line = f"[{utc_ts()}] {msg}\n"
    append_line(path, line)
    if also_print:
        print(line, end="", flush=True)


def load_json(path: Path, default: Any) -> Any:
    if not path.is_file():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def save_json(path: Path, data: Any) -> None:
    write_text(path, json.dumps(data, indent=2) + "\n")
