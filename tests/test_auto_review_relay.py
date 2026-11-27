"""Slice 1 tests for deploy/auto-review-relay.py.

Every test runs the CLI as a subprocess with a temp state dir and --dry, so no
Signal message and no webhook POST leaves the box.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "deploy" / "auto-review-relay.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "auto_review"
T0 = "2026-11-27T06:00:00Z"


def run(tmp_path: Path, args: list[str], payload: dict | None = None,
        label: str | None = "grok-build:10", env_extra: dict | None = None,
        cwd: Path | None = None) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["AUTO_REVIEW_STATE"] = str(tmp_path)
    env.pop("TMUX_PANE", None)
    if label is None:
        env.pop("AUTO_REVIEW_PANE_LABEL", None)
    else:
        env["AUTO_REVIEW_PANE_LABEL"] = label
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        input=json.dumps(payload) if payload is not None else None,
        capture_output=True, text=True, timeout=30, env=env,
        cwd=str(cwd or REPO),
    )


def signal_lines(out: str) -> list[str]:
    return [line for line in out.splitlines() if line.startswith("SIGNAL: ")]


def webhook_lines(out: str) -> list[str]:
    return [line for line in out.splitlines() if line.startswith("WEBHOOK: ")]


def load_payload(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_permission_prompt_sends_one_line(tmp_path: Path) -> None:
    proc = run(tmp_path, ["--hook", "--harness", "grok", "--dry", "--now", T0],
               load_payload("grok_permission_prompt.json"))
    assert proc.returncode == 0
    lines = signal_lines(proc.stdout)
    assert len(lines) == 1
    assert "grok-build:10 grok - approval needed:" in lines[0]
    assert "Read" in lines[0]
    assert "README.md" in lines[0]


def test_webhook_payload_shape(tmp_path: Path) -> None:
    proc = run(tmp_path, ["--hook", "--harness", "grok", "--dry", "--now", T0],
               load_payload("grok_permission_prompt.json"))
    lines = webhook_lines(proc.stdout)
    assert len(lines) == 1
    body = json.loads(lines[0][len("WEBHOOK: "):])
    assert body["kind"] == "auto-review-card"
    assert body["harness"] == "grok"
    assert body["session"] == "grok-build"
    assert body["window"] == "10"
    assert body["needs-CEO"] is True
    assert body["tool"] == "Read"


def test_duplicate_card_is_suppressed(tmp_path: Path) -> None:
    payload = load_payload("grok_permission_prompt.json")
    first = run(tmp_path, ["--hook", "--harness", "grok", "--dry", "--now", T0], payload)
    second = run(tmp_path, ["--hook", "--harness", "grok", "--dry", "--now", T0], payload)
    assert len(signal_lines(first.stdout)) == 1
    assert signal_lines(second.stdout) == []
    assert "dedupe" in (tmp_path / "relay.log").read_text()


def test_non_permission_notification_is_ignored(tmp_path: Path) -> None:
    payload = load_payload("grok_permission_prompt.json")
    payload["notification_type"] = "idle_prompt"
    proc = run(tmp_path, ["--hook", "--harness", "grok", "--dry", "--now", T0], payload)
    assert proc.returncode == 0
    assert proc.stdout == ""


def test_message_without_type_needs_permission_wording(tmp_path: Path) -> None:
    idle = {"message": "Waiting for your input", "tool_name": ""}
    quiet = run(tmp_path, ["--hook", "--harness", "grok", "--dry", "--now", T0], idle)
    assert quiet.stdout == ""
    loud_payload = {
        "cwd": "/home/debian/agent-harness",
        "message": "Needs your permission to use Bash",
        "tool_name": "Bash",
        "tool_input": {"command": "git status --porcelain"},
    }
    loud = run(tmp_path, ["--hook", "--harness", "grok", "--dry", "--now", T0], loud_payload)
    assert len(signal_lines(loud.stdout)) == 1
    assert "git status --porcelain" in loud.stdout


def test_redacts_tokens_and_absolute_paths(tmp_path: Path) -> None:
    payload = load_payload("grok_permission_prompt.json")
    payload["notification_type"] = "permission_prompt"
    payload["tool_input"] = {
        "command": 'curl -H "Authorization: sk-abcdefghijklmnopqrstuv" '
                   "https://example.test/x --out /home/debian/secret/statement.pdf"
    }
    proc = run(tmp_path, ["--hook", "--harness", "grok", "--dry", "--now", T0], payload)
    out = proc.stdout
    assert "sk-abcdefghijklmnop" not in out
    assert "/home/debian" not in out
    assert "statement.pdf" in out


def test_hourly_cap_drops_the_thirteenth(tmp_path: Path) -> None:
    payload = load_payload("grok_permission_prompt.json")
    for index in range(12):
        payload["message"] = f"Grok needs your permission to run Read {index}"
        proc = run(tmp_path, ["--hook", "--harness", "grok", "--dry", "--now", T0], payload)
        assert len(signal_lines(proc.stdout)) == 1
    payload["message"] = "Grok needs your permission to run Read 12"
    capped = run(tmp_path, ["--hook", "--harness", "grok", "--dry", "--now", T0], payload)
    assert signal_lines(capped.stdout) == []
    assert "capped" in (tmp_path / "relay.log").read_text()


def test_disabled_file_stops_everything(tmp_path: Path) -> None:
    (tmp_path / "DISABLED").write_text("", encoding="utf-8")
    proc = run(tmp_path, ["--hook", "--harness", "grok", "--dry", "--now", T0],
               load_payload("grok_permission_prompt.json"))
    assert proc.returncode == 0
    assert proc.stdout == ""
    assert "disabled" in (tmp_path / "relay.log").read_text()


def test_label_falls_back_to_cwd_basename(tmp_path: Path) -> None:
    project = tmp_path / "myproj"
    project.mkdir()
    payload = load_payload("grok_permission_prompt.json")
    payload.pop("cwd", None)
    proc = run(tmp_path, ["--hook", "--harness", "grok", "--dry", "--now", T0],
               payload, label=None, cwd=project)
    assert "myproj grok - approval needed:" in proc.stdout


def test_reminder_fires_once_at_ten_minutes(tmp_path: Path) -> None:
    pane = FIXTURES / "grok_card.txt"
    payload = load_payload("grok_permission_prompt.json")
    payload["message"] = "Confirm HEAD and dirty state of both harness trees"
    first = run(tmp_path, ["--hook", "--harness", "grok", "--dry", "--now", T0], payload)
    assert len(signal_lines(first.stdout)) == 1

    env = {"AUTO_REVIEW_PANE_TEXT_FILE": str(pane)}
    early = run(tmp_path, ["--sweep", "--dry", "--now", "2026-11-27T06:05:00Z"],
                env_extra=env)
    assert early.stdout == ""

    remind = run(tmp_path, ["--sweep", "--dry", "--now", "2026-11-27T06:10:01Z"],
                 env_extra=env)
    assert len(signal_lines(remind.stdout)) == 1
    assert "approval needed" in remind.stdout

    again = run(tmp_path, ["--sweep", "--dry", "--now", "2026-11-27T06:20:00Z"],
                env_extra=env)
    assert again.stdout == ""


def test_resolved_card_drops_state(tmp_path: Path) -> None:
    pane = tmp_path / "resolved.txt"
    pane.write_text("no card here\n", encoding="utf-8")
    payload = load_payload("grok_permission_prompt.json")
    payload["message"] = "Confirm HEAD and dirty state of both harness trees"
    run(tmp_path, ["--hook", "--harness", "grok", "--dry", "--now", T0], payload)

    sweep = run(tmp_path, ["--sweep", "--dry", "--now", "2026-11-27T06:10:01Z"],
                env_extra={"AUTO_REVIEW_PANE_TEXT_FILE": str(pane)})
    assert sweep.stdout == ""
    state = json.loads((tmp_path / "state.json").read_text())
    assert state["rows"] == {}
    assert "resolved" in (tmp_path / "relay.log").read_text()


def test_bad_json_exits_zero(tmp_path: Path) -> None:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--hook", "--harness", "grok", "--dry"],
        input="not json", capture_output=True, text=True, timeout=30,
        env={**os.environ, "AUTO_REVIEW_STATE": str(tmp_path)},
    )
    assert proc.returncode == 0
    assert "bad-json" in (tmp_path / "relay.log").read_text()


def test_signal_text_is_one_short_line(tmp_path: Path) -> None:
    payload = load_payload("grok_permission_prompt.json")
    payload["message"] = "x" * 900
    proc = run(tmp_path, ["--hook", "--harness", "grok", "--dry", "--now", T0], payload)
    line = signal_lines(proc.stdout)[0]
    assert len(line) <= len("SIGNAL: ") + 300
    assert "\n" not in line
