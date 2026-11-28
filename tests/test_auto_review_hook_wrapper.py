"""Slice 2 tests for the Grok Notification hook wrapper.

The wrapper must forward stdin unchanged, stay silent, and exit 0 whatever
happens to the relay.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
WRAPPER = REPO / "deploy" / "hooks" / "grok-auto-review-relay.sh"
RELAY = REPO / "deploy" / "auto-review-relay.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "auto_review"
T0 = "2026-11-27T06:00:00Z"


def run_wrapper(payload: dict | None, extra: dict | None = None,
                timeout: int = 30) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env.pop("AUTO_REVIEW_PANE_LABEL", None)
    env.pop("TMUX_PANE", None)
    if extra:
        env.update(extra)
    return subprocess.run(
        ["bash", str(WRAPPER)],
        input=json.dumps(payload) if payload is not None else "",
        capture_output=True, text=True, timeout=timeout, env=env,
    )


def fake_relay(tmp_path: Path, body: str) -> tuple[Path, Path, Path]:
    relay = tmp_path / "fake_relay.py"
    relay.write_text(body, encoding="utf-8")
    capture = tmp_path / "stdin.txt"
    argv = tmp_path / "argv.json"
    return relay, capture, argv


def test_wrapper_forwards_stdin_and_args(tmp_path: Path) -> None:
    relay, capture, argv = fake_relay(
        tmp_path,
        "import json, os, sys\n"
        "open(os.environ['CAPTURE'], 'w').write(sys.stdin.read())\n"
        "open(os.environ['ARGV'], 'w').write(json.dumps(sys.argv[1:]))\n",
    )
    payload = json.loads((FIXTURES / "grok_permission_prompt.json").read_text())
    proc = run_wrapper(payload, {
        "AUTO_REVIEW_RELAY": str(relay),
        "AUTO_REVIEW_PYTHON": sys.executable,
        "CAPTURE": str(capture),
        "ARGV": str(argv),
    })
    assert proc.returncode == 0
    assert proc.stdout == ""
    assert json.loads(capture.read_text()) == payload
    assert json.loads(argv.read_text()) == ["--hook", "--harness", "grok"]


def test_wrapper_adds_dry_flag(tmp_path: Path) -> None:
    relay, capture, argv = fake_relay(
        tmp_path,
        "import json, os, sys\n"
        "open(os.environ['ARGV'], 'w').write(json.dumps(sys.argv[1:]))\n",
    )
    run_wrapper({"message": "x"}, {
        "AUTO_REVIEW_RELAY": str(relay),
        "AUTO_REVIEW_PYTHON": sys.executable,
        "ARGV": str(argv),
        "AUTO_REVIEW_DRY": "1",
    })
    assert json.loads(argv.read_text()) == ["--hook", "--harness", "grok", "--dry"]


def test_missing_relay_is_silent_and_zero(tmp_path: Path) -> None:
    proc = run_wrapper({"message": "x"},
                       {"AUTO_REVIEW_RELAY": str(tmp_path / "absent.py")})
    assert proc.returncode == 0
    assert proc.stdout == ""
    assert proc.stderr == ""


def test_hung_relay_is_killed_quickly(tmp_path: Path) -> None:
    relay, capture, argv = fake_relay(tmp_path, "import time\ntime.sleep(30)\n")
    started = time.monotonic()
    proc = run_wrapper({"message": "x"}, {
        "AUTO_REVIEW_RELAY": str(relay),
        "AUTO_REVIEW_PYTHON": sys.executable,
        "AUTO_REVIEW_TIMEOUT": "1",
    })
    elapsed = time.monotonic() - started
    assert proc.returncode == 0
    assert elapsed < 10


def test_hook_registration_points_at_the_wrapper() -> None:
    doc = json.loads((REPO / "deploy" / "hooks" / "grok-notification.json").read_text())
    handlers = doc["hooks"]["Notification"][0]["hooks"]
    assert handlers[0]["command"].endswith("/.grok/hooks/auto-review-relay.sh")
    assert handlers[0]["type"] == "command"
    assert handlers[0]["timeout"] >= 5


def test_wrapper_end_to_end_ignores_non_permission(tmp_path: Path) -> None:
    payload = json.loads((FIXTURES / "grok_permission_prompt.json").read_text())
    payload["notification_type"] = "idle_prompt"
    proc = run_wrapper(payload, {
        "AUTO_REVIEW_RELAY": str(RELAY),
        "AUTO_REVIEW_PYTHON": sys.executable,
        "AUTO_REVIEW_STATE": str(tmp_path),
        "AUTO_REVIEW_PANE_LABEL": "grok-build:10",
        "AUTO_REVIEW_DRY": "1",
    })
    assert proc.returncode == 0
    state_file = tmp_path / "state.json"
    if state_file.exists():
        assert json.loads(state_file.read_text())["rows"] == {}


def test_wrapper_end_to_end_records_permission_card(tmp_path: Path) -> None:
    payload = json.loads((FIXTURES / "grok_permission_prompt.json").read_text())
    proc = run_wrapper(payload, {
        "AUTO_REVIEW_RELAY": str(RELAY),
        "AUTO_REVIEW_PYTHON": sys.executable,
        "AUTO_REVIEW_STATE": str(tmp_path),
        "AUTO_REVIEW_PANE_LABEL": "grok-build:10",
        "AUTO_REVIEW_DRY": "1",
    })
    assert proc.returncode == 0
    assert proc.stdout == ""
    state = json.loads((tmp_path / "state.json").read_text())
    assert len(state["rows"]) == 1
    row = next(iter(state["rows"].values()))
    assert row["harness"] == "grok"
    assert row["label"] == "grok-build:10"
