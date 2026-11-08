"""AC-1..AC-4: ops-dashboard unit and registry contract, no directive change."""
from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEPLOY_SERVICE = ROOT / "deploy" / "ops-dashboard.service"
DEPLOY_TIMER = ROOT / "deploy" / "ops-dashboard.timer"
LIVE_SERVICE = Path("/etc/systemd/system/ops-dashboard.service")
LIVE_TIMER = Path("/etc/systemd/system/ops-dashboard.timer")
REGISTRY = Path(
    "/opt/second-brain/vault/agent-tasks/ops/SYSTEMD-TIMERS-INVENTORY.md"
)

BASE_CALENDARS = (
    "OnCalendar=*-*-* 01:00:00 UTC",
    "OnCalendar=*-*-* 12:00:00 UTC",
)
FOUR_CALENDAR_MARKS = (
    "01:00:00 UTC",
    "12:00:00 UTC",
    "19:45:00 UTC",
    "23:45:00 UTC",
)


def _directive_lines(text: str, key: str) -> list[str]:
    return [ln.strip() for ln in text.splitlines() if ln.startswith(key)]


class TestOpsDashboardContract(unittest.TestCase):
    def test_ac_1_exit_2_is_intentional_red(self):
        """AC-1: SuccessExitStatus=0 2 stays, and the unit says exit 2 is RED."""
        for path in (DEPLOY_SERVICE, LIVE_SERVICE):
            text = path.read_text(encoding="utf-8")
            self.assertEqual(
                _directive_lines(text, "SuccessExitStatus="),
                ["SuccessExitStatus=0 2"],
                path,
            )
            self.assertIn("intentional RED", text, path)
            self.assertIn("SuccessExitStatus=0 2", text, path)
            self.assertIn(
                "ExecStart=/usr/bin/python3 /home/debian/agent-harness/scripts/ops_dashboard.py --write",
                text,
                path,
            )

    def test_ac_2_timer_enabled_with_four_calendars(self):
        """AC-2: four calendars are named; the base file still has two OnCalendar lines."""
        for path in (DEPLOY_TIMER, LIVE_TIMER):
            text = path.read_text(encoding="utf-8")
            self.assertEqual(
                _directive_lines(text, "OnCalendar="),
                list(BASE_CALENDARS),
                path,
            )
            lowered = text.lower()
            self.assertIn("enabled", lowered, path)
            self.assertIn("four", lowered, path)
            for mark in FOUR_CALENDAR_MARKS:
                self.assertIn(mark, text, path)
            self.assertIn("Sun,Mon,Tue,Wed,Thu", text, path)

    def test_ac_3_registry_entry_matches_the_unit(self):
        """AC-3: the inventory row documents the same contract."""
        text = REGISTRY.read_text(encoding="utf-8")
        self.assertIn("ops-dashboard.timer", text)
        self.assertIn("ops-dashboard.service", text)
        self.assertIn("intentional RED", text)
        self.assertIn("SuccessExitStatus=0 2", text)
        self.assertIn("enabled", text.lower())
        for mark in FOUR_CALENDAR_MARKS:
            self.assertIn(mark, text)
        self.assertIn("Sun,Mon,Tue,Wed,Thu", text)

    def test_ac_4_loaded_unit_unchanged(self):
        """AC-4: loaded timer stays enabled with the same four calendars."""
        show = subprocess.run(
            [
                "systemctl",
                "show",
                "ops-dashboard.service",
                "ops-dashboard.timer",
                "-p",
                "SuccessExitStatus",
                "-p",
                "UnitFileState",
                "-p",
                "TimersCalendar",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(show.returncode, 0, show.stderr)
        text = show.stdout
        self.assertIn("SuccessExitStatus=0 2", text)
        self.assertIn("UnitFileState=enabled", text)
        for mark in (
            "01:00:00 UTC",
            "12:00:00 UTC",
            "19:45:00 UTC",
            "23:45:00 UTC",
        ):
            self.assertIn(mark, text)
        self.assertEqual(text.count("OnCalendar="), 4)
