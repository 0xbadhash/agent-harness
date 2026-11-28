"""Tests for the glossary artifact gate (AC-1 and AC-4 data)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import check_glossary as glossary  # noqa: E402


def _write(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "docs" / "glossary.md"
    path.parent.mkdir(parents=True)
    path.write_text(body, encoding="utf-8")
    return path


def test_valid_table_passes(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "| Term | Definition | Owner |\n"
        "|---|---|---|\n"
        "| Door | Reversible or not. | templates/PR_DRAFT.md |\n"
        "| Ticket | One tracer bullet. | scripts/run_tickets.py |\n",
    )
    report = glossary.check(tmp_path)
    assert report.ok and report.terms == 2
    assert glossary.main(["--root", str(tmp_path)]) == 0


def test_duplicate_normalized_term_fails(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "| Term | Definition | Owner |\n"
        "|---|---|---|\n"
        "| Ship FSM | Flow. | scripts/next_skill.py |\n"
        "| ship-fsm | Same. | scripts/next_skill.py |\n",
    )
    report = glossary.check(tmp_path)
    assert not report.ok
    assert any("collides" in finding for finding in report.findings)
    assert glossary.main(["--root", str(tmp_path)]) == 1


def test_row_without_definition_fails(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "| Term | Definition | Owner |\n"
        "|---|---|---|\n"
        "| Door |  |  |\n",
    )
    report = glossary.check(tmp_path)
    assert not report.ok
    assert any("needs a definition" in finding for finding in report.findings)


def test_missing_file_skips(tmp_path: Path) -> None:
    report = glossary.check(tmp_path)
    assert report.ok and report.skip and "no glossary" in report.skip
    assert glossary.main(["--root", str(tmp_path)]) == 0
