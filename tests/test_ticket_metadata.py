"""Ticket metadata: dependency parsing, Touches, and Session write-back."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_ticket_dag as dag  # noqa: E402
import run_tickets  # noqa: E402


def _write(directory: Path, name: str, body: str) -> Path:
    path = directory / name
    path.write_text(body, encoding="utf-8")
    return path


def test_none_with_a_note_is_not_a_dependency() -> None:
    assert dag._ids("None — can start immediately") == []
    assert dag._ids("None - can start immediately") == []


def test_dependency_with_a_note_keeps_the_id() -> None:
    assert dag._ids("02 — after the schema lands") == ["02"]
    assert dag._ids("01, 02 — both must land") == ["01", "02"]


def test_load_tickets_parses_touches(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "01-a.md",
        "# 01 — a\n\n**Kind:** feature\n**Prefactor:** none\n"
        "**Touches:** `scripts/a.py`, docs/a.md\n"
        "**Blocked by:** None — can start immediately\n**Status:** ready-for-agent\n",
    )
    tickets = dag.load_tickets(tmp_path)
    assert tickets["01"]["touches"] == ["scripts/a.py", "docs/a.md"]
    assert tickets["01"]["deps"] == []


def test_record_session_inserts_after_status(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        "01-a.md",
        "# 01 — a\n\n**Blocked by:** None\n**Status:** ready-for-agent\n",
    )
    run_tickets.record_session(tmp_path, "01", "sess-42")
    text = path.read_text(encoding="utf-8")
    assert "**Session:** sess-42" in text
    assert text.index("**Status:**") < text.index("**Session:**")


def test_record_session_replaces_existing_value(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        "01-a.md",
        "# 01 — a\n\n**Status:** ready-for-agent\n**Session:** none\n",
    )
    run_tickets.record_session(tmp_path, "01", "sess-7")
    text = path.read_text(encoding="utf-8")
    assert text.count("**Session:**") == 1
    assert "**Session:** sess-7" in text


def test_dry_run_does_not_write_session(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        "01-a.md",
        "# 01 — a\n\n**Blocked by:** None\n**Status:** ready-for-agent\n",
    )
    run_tickets.run_ticket_set(tmp_path, lambda tid, d: "sess", dry_run=True)
    assert "**Session:**" not in path.read_text(encoding="utf-8")


def test_real_run_writes_session(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        "01-a.md",
        "# 01 — a\n\n**Blocked by:** None\n**Status:** ready-for-agent\n",
    )
    run_tickets.run_ticket_set(tmp_path, lambda tid, d: "sess-9", workers=1)
    assert "**Session:** sess-9" in path.read_text(encoding="utf-8")
