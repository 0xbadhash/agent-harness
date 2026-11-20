#!/usr/bin/env python3
"""Local fixture screenshot. Skip only when Playwright cannot be imported."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PNG = ROOT / ".agents" / "artifacts" / "feature-shots" / "fixture-S0.png"


def test_base_url_rejects_remote_host():
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "web_feature_shots.py"),
            "--root",
            str(ROOT / "fixtures" / "product_traits" / "web3_no_isolation"),
            "--base-url",
            "http://example.com",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert "SKIP playwright missing" not in result.stdout


def test_fixture_png_when_playwright_imports():
    pytest.importorskip("playwright")
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "web_feature_shots.py"),
            "--root",
            str(ROOT / "fixtures" / "product_traits" / "web3_no_isolation"),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=45,
    )
    if result.returncode == 2 and "SKIP" in (result.stdout + result.stderr):
        pytest.skip(result.stdout.strip() or result.stderr.strip())
    assert result.returncode == 0, result.stdout + result.stderr
    data = PNG.read_bytes()
    assert data.startswith(b"\x89PNG")
    assert data[12:16] == b"IHDR"
    width = int.from_bytes(data[16:20], "big")
    height = int.from_bytes(data[20:24], "big")
    assert width > 0 and height > 0
    assert len(data) >= 1024
