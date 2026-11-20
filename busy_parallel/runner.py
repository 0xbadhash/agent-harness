"""DRY-RUN runner. Reads one JSON event from a file path argv[1] or stdin."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from busy_parallel.decide import decide
from busy_parallel.launch import run
from busy_parallel import state as st


def load_cfg(home: Path) -> dict:
    path = Path(os.environ.get("BUSY_PARALLEL_CONFIG", home / "busy-parallel.yaml"))
    if not path.is_file():
        return {}
    try:
        import yaml  # optional; JSON is the stdlib path
    except ImportError:
        yaml = None
    raw = path.read_text(encoding="utf-8")
    if path.suffix == ".json" or yaml is None:
        return json.loads(raw)
    data = yaml.safe_load(raw)
    return data if isinstance(data, dict) else {}


def handle(event: dict, home: Path, cfg: dict | None = None) -> dict:
    cfg = cfg if cfg is not None else load_cfg(home)
    decision = decide(event, cfg, home)
    result = {"launch": decision.launch, "reason": decision.reason, "job_id": decision.job_id}
    if not decision.launch:
        sys.stderr.write(f"busy-parallel skip {decision.reason}\n")
        return result
    mode = os.environ.get("BUSY_PARALLEL_MODE", "dry")
    try:
        launched = run(home, cfg, decision.job_id, event.get("text") or "", mode)
    except Exception as exc:  # noqa: BLE001 — fail open, chief keeps the message
        sys.stderr.write(f"busy-parallel kick-failed {type(exc).__name__}\n")
        result["launch"] = False
        result["reason"] = "kick-failed"
        return result
    st.mark_seen(home, str(event.get("message_id")))
    st.add_inflight(home, decision.job_id)
    st.mark_launch(home)
    result["kick_sha"] = launched["kick_sha"]
    result["launched"] = bool(launched["launched"])
    result["handled"] = mode == "live" and launched["launched"]
    sys.stderr.write(f"busy-parallel {mode} {decision.reason} {decision.job_id}\n")
    return result


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    home = Path(os.environ.get("HERMES_HOME", "/tmp/busy-parallel-unset")).resolve()
    raw = Path(argv[0]).read_text(encoding="utf-8") if argv else sys.stdin.read()
    event = json.loads(raw)
    print(json.dumps(handle(event, home)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
