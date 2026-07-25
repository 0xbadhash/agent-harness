"""TDD: product venv interpreter must keep Unix .venv path (absolute, not resolve).

Night-shift / product_smoke regressions: Path.resolve() collapses
.venv/bin/python → /usr/bin/python3 and drops site-packages (pytest missing).
Windows must prefer Scripts\\python.exe.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))


def test_product_venv_python_keeps_posix_symlink_under_venv(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    import product_venv as pv  # type: ignore

    monkeypatch.setattr(sys, "platform", "linux")
    vbin = tmp_path / ".venv" / "bin"
    vbin.mkdir(parents=True)
    base = tmp_path / "base_python"
    base.write_bytes(b"#!/bin/sh\n")
    base.chmod(0o755)
    (vbin / "python").symlink_to(base)

    got = pv.product_venv_python(tmp_path)
    assert got is not None
    assert ".venv" in got.parts
    collapsed = (tmp_path / ".venv" / "bin" / "python").resolve()
    assert collapsed == base.resolve()
    assert got != collapsed  # absolute() path, not resolve()


def test_product_venv_python_windows_scripts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    import product_venv as pv  # type: ignore

    monkeypatch.setattr(sys, "platform", "win32")
    scripts = tmp_path / ".venv" / "Scripts"
    scripts.mkdir(parents=True)
    (scripts / "python.exe").write_bytes(b"MZ")

    got = pv.product_venv_python(tmp_path)
    assert got is not None
    assert got.name.lower() == "python.exe"
    assert "Scripts" in got.parts


def test_rewrite_smoke_python_uses_venv(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    import product_venv as pv  # type: ignore

    monkeypatch.setattr(sys, "platform", "linux")
    vbin = tmp_path / ".venv" / "bin"
    vbin.mkdir(parents=True)
    py = vbin / "python"
    py.write_bytes(b"#!/bin/sh\n")
    py.chmod(0o755)

    cmd = pv.rewrite_smoke_python(
        ["python", "-m", "pytest", "tests/", "-q"], tmp_path
    )
    assert ".venv" in cmd[0]
    assert cmd[1:] == ["-m", "pytest", "tests/", "-q"]


def test_rewrite_leaves_absolute_alone(tmp_path: Path):
    import product_venv as pv  # type: ignore

    cmd = pv.rewrite_smoke_python(["/usr/bin/python3", "-c", "pass"], tmp_path)
    assert cmd[0] == "/usr/bin/python3"


def test_product_venv_python_missing(tmp_path: Path):
    import product_venv as pv  # type: ignore

    assert pv.product_venv_python(tmp_path) is None


def test_night_shift_venv_python_keeps_symlink(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """night_shift_readiness._venv_python must not collapse to system path."""
    import night_shift_readiness as nsr  # type: ignore

    monkeypatch.setattr(sys, "platform", "linux")
    vbin = tmp_path / ".venv" / "bin"
    vbin.mkdir(parents=True)
    base = tmp_path / "base_python"
    base.write_bytes(b"#!/bin/sh\n")
    base.chmod(0o755)
    (vbin / "python").symlink_to(base)

    got = nsr._venv_python(tmp_path)
    assert ".venv" in Path(got).parts
    assert Path(got).resolve() == base.resolve()
    assert Path(got) != Path(got).resolve() or str(got).endswith(
        str(Path(".venv") / "bin" / "python")
    )
    # Stronger: string must contain .venv
    assert "/.venv/" in got.replace("\\", "/") or got.endswith(".venv/bin/python")
