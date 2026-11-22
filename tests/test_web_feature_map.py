#!/usr/bin/env python3
"""Fixture feature map names S0 and the smoke-load proof."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_fixture_stdout_contains_s0_and_smoke_load():
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "web_feature_map.py"),
            "--root",
            str(ROOT / "fixtures" / "product_traits" / "web3_no_isolation"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "S0" in result.stdout
    assert "Smoke load" in result.stdout
