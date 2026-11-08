"""Night-shift must not destroy the operator's backlog, and the hardcode gate must
tell a bare id from a credential."""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import check_hardcodes  # noqa: E402
from night_shift_readiness import merge_human_backlog  # noqa: E402


def test_human_backlog_survives_regeneration(tmp_path: Path) -> None:
    todo = tmp_path / "TODO.md"
    todo.write_text(
        "# p TODO\n\n## Auto recommendations\n\n- [ ] old auto line\n\n"
        "## Human backlog\n\n- [ ] keep me\n- [ ] and me\n",
        encoding="utf-8",
    )
    generated = "# p TODO\n\n## Auto recommendations\n\n- [ ] new auto line\n\n## Human backlog\n"
    merged = merge_human_backlog(todo, generated)
    assert "new auto line" in merged
    assert "old auto line" not in merged
    assert "keep me" in merged and "and me" in merged


def test_missing_previous_file_is_fine(tmp_path: Path) -> None:
    generated = "# p TODO\n\n## Human backlog\n"
    assert merge_human_backlog(tmp_path / "nope.md", generated) == generated


def _scan(_tmp_path: Path, files: dict[str, str]) -> int:
    # pytest's tmp dir sits under the agent cache, which the scanner skips
    root = Path(tempfile.mkdtemp(dir="/tmp", prefix="hc-"))
    try:
        for name, body in files.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body, encoding="utf-8")
        return check_hardcodes.scan_root(root)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_bare_onedrive_id_is_not_a_credential(tmp_path: Path, capsys) -> None:
    payload = {"SSSM": {"drive_id": "c8748b4546461f49", "parent_id": "C8748B4546461F49!1404"}}
    assert _scan(tmp_path, {"data/onedrive_children.json": json.dumps(payload)}) == 0
    assert "exposed_api_key" not in capsys.readouterr().out


def test_assigned_key_is_still_flagged(tmp_path: Path, capsys) -> None:
    body = 'API_KEY = "C8748B4546461F49"\n'
    assert _scan(tmp_path, {"config.py": body}) == 1
    assert "exposed_api_key" in capsys.readouterr().out


def test_vendored_challenge_copy_is_skipped(tmp_path: Path) -> None:
    body = 'ENV = "/home/debian/hermes/.env"\n'
    assert _scan(tmp_path, {"scripts/challenge.py": body}) == 0


def test_validate_offers_skip_hardcodes() -> None:
    out = subprocess.run([sys.executable, str(ROOT / "scripts" / "validate.py"), "--help"],
                         capture_output=True, text=True, check=False).stdout
    assert "--skip-hardcodes" in out
