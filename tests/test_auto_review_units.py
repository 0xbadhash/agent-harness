"""Slice 4 tests: systemd units and hook registration for the auto-review relay.

These only read the templates in deploy/. They do not require systemd, and they
never install anything.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DEPLOY = REPO / "deploy"
RELAY = "/opt/catalyxt/ops/auto-review-relay.py"


def text(name: str) -> str:
    return (DEPLOY / name).read_text(encoding="utf-8")


def test_watch_service_runs_the_watch_loop() -> None:
    body = text("auto-review-relay-watch.service")
    assert f"ExecStart=/usr/bin/python3 {RELAY} --watch --interval 20" in body
    assert "Restart=on-failure" in body
    assert "WantedBy=default.target" in body


def test_digest_service_is_oneshot() -> None:
    body = text("auto-review-relay-digest.service")
    assert "Type=oneshot" in body
    assert f"ExecStart=/usr/bin/python3 {RELAY} --digest" in body


def test_digest_timer_fires_once_daily_and_names_its_unit() -> None:
    body = text("auto-review-relay-digest.timer")
    assert "OnCalendar=*-*-* 00:00:00 UTC" in body
    assert "Unit=auto-review-relay-digest.service" in body
    assert "Persistent=true" in body


def test_digest_timer_calendar_parses_with_systemd() -> None:
    tool = shutil.which("systemd-analyze")
    if tool is None:
        return
    proc = subprocess.run(
        [tool, "calendar", "*-*-* 00:00:00 UTC"],
        capture_output=True, text=True, timeout=30, check=False,
    )
    assert proc.returncode == 0
    assert "00:00:00" in proc.stdout


def test_hook_registration_points_at_the_installed_wrapper() -> None:
    data = json.loads(text("hooks/grok-notification.json"))
    entries = data["hooks"]["Notification"]
    handlers = [h for entry in entries for h in entry["hooks"]]
    targets = [h["command"] for h in handlers]
    assert targets == ["/home/debian/.grok/hooks/auto-review-relay.sh"]
    assert all(h["type"] == "command" for h in handlers)
    assert all(int(h["timeout"]) <= 10 for h in handlers)
