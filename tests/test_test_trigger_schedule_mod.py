"""Embed test_trigger_schedule module."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from test_trigger_schedule import ROWS, schedule_markdown  # noqa: E402


def test_has_ship_and_night():
    md = schedule_markdown()
    assert "/pr_review" in md
    assert "Night shift" in md
    assert "daytime-gates" in md
    assert "code_review" in md
    assert len(ROWS) >= 8


def test_compact():
    assert "Phase" in schedule_markdown(compact=True)
