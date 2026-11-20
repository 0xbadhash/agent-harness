"""Write a kick file. Exec only when mode is live and BUSY_PARALLEL_KICK is set."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

from busy_parallel import MARKER
from busy_parallel import state as st


def kick_text(user_text: str) -> str:
    return (
        "You are a parallel worker for one CEO DM that arrived while chief-of-staff "
        "was busy. Reply only to that DM through this profile's normal outbound. "
        "Do not send anywhere else. Do not restart services. Do not pass --yolo. "
        f"Do not echo the marker {MARKER}.\n\n"
        f"CEO message:\n{user_text.strip()}\n"
    )


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(home: Path, job_id: str, user_text: str) -> dict:
    root = st.state_dir(home) / "jobs" / job_id
    root.mkdir(parents=True, exist_ok=True)
    kick = root / "kick.txt"
    kick.write_text(kick_text(user_text), encoding="utf-8")
    expect = root / "expect.txt"
    expect.write_text(f"job {job_id} reply only to the CEO DM\n", encoding="utf-8")
    log = root / "worker.log"
    return {
        "kick": kick,
        "expect": expect,
        "log": log,
        "kick_sha": sha256_file(kick),
    }


def argv(kick_bin: str, profile: str, job_id: str, prepared: dict, max_turns: int) -> list:
    return [
        kick_bin,
        "--job-id", job_id,
        "--profile", profile,
        "--kick", str(prepared["kick"]),
        "--kick-sha", prepared["kick_sha"],
        "--max-turns", str(max_turns),
        "--log", str(prepared["log"]),
        "--expect", str(prepared["expect"]),
    ]


def run(home: Path, cfg: dict, job_id: str, user_text: str, mode: str) -> dict:
    """mode dry writes the kick and returns. mode live execs the kick stub."""
    prepared = prepare(home, job_id, user_text)
    profile = str(cfg.get("profile") or "chief-of-staff")
    turns = int(cfg.get("max_turns") or 4)
    kick_bin = os.environ.get("BUSY_PARALLEL_KICK", "hermes-kick.sh")
    cmd = argv(kick_bin, profile, job_id, prepared, turns)
    if "--yolo" in cmd:
        raise RuntimeError("refusing --yolo")
    record = {
        "job_id": job_id,
        "mode": mode,
        "argv": cmd,
        "kick_sha": prepared["kick_sha"],
        "launched": False,
    }
    out = st.state_dir(home) / "would-launch" / f"{job_id}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    if mode != "live":
        out.write_text(json.dumps(record), encoding="utf-8")
        return record
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    record["launched"] = proc.returncode == 0
    record["returncode"] = proc.returncode
    out.write_text(json.dumps({k: v for k, v in record.items() if k != "argv"} | {"argv": cmd}), encoding="utf-8")
    if proc.returncode != 0:
        raise RuntimeError(f"kick exit {proc.returncode}")
    return record
