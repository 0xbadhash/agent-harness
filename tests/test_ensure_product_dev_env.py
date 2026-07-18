#!/usr/bin/env python3
"""TDD: product .venv + requirements-dev preflight for night_shift_all."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load():
    path = ROOT / "scripts" / "ensure_product_dev_env.py"
    if not path.is_file():
        pytest.fail("missing scripts/ensure_product_dev_env.py")
    spec = importlib.util.spec_from_file_location("ensure_product_dev_env", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def mod():
    return _load()


def test_ok_when_pytest_importable(mod, tmp_path: Path, monkeypatch):
    # Use current interpreter which has pytest (test runner)
    r = mod.ensure_product_dev_env(tmp_path, python=sys.executable, dry_run=False)
    assert r["status"] in ("ok", "skip")
    assert r["ok"] is True


def test_creates_venv_and_installs_when_requirements_dev(mod, tmp_path: Path, monkeypatch):
    (tmp_path / "requirements-dev.txt").write_text("pytest>=7\n", encoding="utf-8")
    calls: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        calls.append(list(cmd))

        class R:
            returncode = 0
            stdout = ""
            stderr = ""

        return R()

    monkeypatch.setattr(mod.subprocess, "run", fake_run)

    # Fail import until "install" calls have run; then succeed (post-pip check)
    state = {"n": 0}

    def can_import(py, names):
        state["n"] += 1
        # First call: pre-check missing; later: after pip
        return state["n"] > 1

    monkeypatch.setattr(mod, "_can_import", can_import)

    r = mod.ensure_product_dev_env(tmp_path, python=sys.executable, dry_run=False)
    assert r["ok"] is True, r
    assert r["status"] == "installed"
    # venv create + pip install
    joined = [" ".join(c) for c in calls]
    assert any("venv" in j for j in joined)
    assert any("pip" in j and "install" in j for j in joined)


def test_skip_when_no_requirements_and_missing_pytest(mod, tmp_path: Path, monkeypatch):
    monkeypatch.setattr(mod, "_can_import", lambda py, names: False)
    r = mod.ensure_product_dev_env(tmp_path, python=sys.executable, dry_run=False)
    assert r["status"] == "skip"
    assert r["ok"] is True  # skip is not hard fail; readiness may still fail


def test_dry_run_does_not_pip(mod, tmp_path: Path, monkeypatch):
    (tmp_path / "requirements-dev.txt").write_text("pytest\n", encoding="utf-8")
    monkeypatch.setattr(mod, "_can_import", lambda py, names: False)
    calls: list = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)

        class R:
            returncode = 0
            stdout = ""
            stderr = ""

        return R()

    monkeypatch.setattr(mod.subprocess, "run", fake_run)
    r = mod.ensure_product_dev_env(tmp_path, python=sys.executable, dry_run=True)
    assert r["status"] == "dry-run"
    assert calls == []
