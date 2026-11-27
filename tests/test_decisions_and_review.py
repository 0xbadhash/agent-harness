"""Tests for the ADR spine, door-aware review, and the prefactor rule.

Covers AC-1 from the top-50 completion spec.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import check_adr  # noqa: E402
import check_ticket_dag  # noqa: E402
import spec_gate  # noqa: E402


def _adr(number: str = "001", *, tradeoff: bool = True, listed: bool = True) -> str:
    body = (
        f"# ADR {number} — test decision\n\n"
        "**Status:** accepted\n"
        "**Date:** 2026-11-27\n\n"
        "## Consequences\n\n"
        "- **Reversibility:** easy to revert.\n"
        "- **Surprise:** a reader may expect otherwise.\n"
    )
    if tradeoff:
        body += "- **Tradeoff:** less speed for more safety.\n"
    return body


def _write_spine(tmp_path: Path, *, tradeoff: bool = True, listed: bool = True) -> Path:
    decisions = tmp_path / ".agents" / "decisions"
    decisions.mkdir(parents=True)
    (decisions / "000-template.md").write_text("# ADR NNN — template\n", encoding="utf-8")
    (decisions / "001-test.md").write_text(_adr(tradeoff=tradeoff), encoding="utf-8")
    index = "# Decisions\n\n| ADR | Title | Status |\n|---|---|---|\n"
    if listed:
        index += "| [001](001-test.md) | Test | accepted |\n"
    (decisions / "README.md").write_text(index, encoding="utf-8")
    return decisions


def test_adr_spine_valid(tmp_path: Path) -> None:
    _write_spine(tmp_path)
    ok, msgs = check_adr.check(tmp_path, strict=True)
    assert ok, msgs


def test_adr_missing_tradeoff_fails(tmp_path: Path) -> None:
    _write_spine(tmp_path, tradeoff=False)
    ok, msgs = check_adr.check(tmp_path)
    assert not ok
    assert any("tradeoff" in m for m in msgs)


def test_adr_missing_from_index_fails(tmp_path: Path) -> None:
    _write_spine(tmp_path, listed=False)
    ok, msgs = check_adr.check(tmp_path)
    assert not ok
    assert any("not listed" in m for m in msgs)


def test_adr_empty_spine_is_advisory_unless_strict(tmp_path: Path) -> None:
    decisions = tmp_path / ".agents" / "decisions"
    decisions.mkdir(parents=True)
    (decisions / "README.md").write_text("# Decisions\n", encoding="utf-8")
    assert check_adr.check(tmp_path)[0]
    assert not check_adr.check(tmp_path, strict=True)[0]


def test_repo_spine_is_valid() -> None:
    ok, msgs = check_adr.check(ROOT, strict=True)
    assert ok, msgs


def test_prefactor_required_for_shared_component(tmp_path: Path) -> None:
    ticket = tmp_path / "01-shared.md"
    ticket.write_text(
        "# 01 — shared\n\n**Kind:** shared-component\n**Prefactor:** none\n"
        "**Blocked by:** None\n",
        encoding="utf-8",
    )
    tickets = check_ticket_dag.load_tickets(tmp_path)
    failures = check_ticket_dag.validate_prefactors(tickets)
    assert failures and "prefactor" in failures[0].lower()


def test_prefactor_becomes_a_blocking_edge(tmp_path: Path) -> None:
    (tmp_path / "01-extract.md").write_text(
        "# 01 — extract\n\n**Kind:** feature\n**Prefactor:** none\n**Blocked by:** None\n",
        encoding="utf-8",
    )
    (tmp_path / "02-use.md").write_text(
        "# 02 — use\n\n**Kind:** shared-component\n**Prefactor:** 01\n"
        "**Blocked by:** None\n",
        encoding="utf-8",
    )
    tickets = check_ticket_dag.load_tickets(tmp_path)
    assert check_ticket_dag.validate_prefactors(tickets) == []
    assert tickets["02"]["deps"] == ["01"]
    assert check_ticket_dag.ready_frontier(tickets) == ["01"]


def test_ticket_dag_accepts_a_diamond(tmp_path: Path) -> None:
    """Two tickets may share one blocker without the DFS reporting a false cycle."""
    (tmp_path / "01-base.md").write_text("# 01 — base\n\n**Blocked by:** None\n",
                                         encoding="utf-8")
    (tmp_path / "02-left.md").write_text("# 02 — left\n\n**Blocked by:** 01\n",
                                         encoding="utf-8")
    (tmp_path / "03-right.md").write_text("# 03 — right\n\n**Blocked by:** 01\n",
                                          encoding="utf-8")
    (tmp_path / "04-join.md").write_text("# 04 — join\n\n**Blocked by:** 02, 03\n",
                                         encoding="utf-8")
    tickets = check_ticket_dag.load_tickets(tmp_path)
    assert check_ticket_dag.find_cycle(tickets) is None
    assert check_ticket_dag.ready_frontier(tickets) == ["01"]


def test_missing_prefactor_ticket_fails(tmp_path: Path) -> None:
    (tmp_path / "01-use.md").write_text(
        "# 01 — use\n\n**Kind:** shared-component\n**Prefactor:** 09\n"
        "**Blocked by:** None\n",
        encoding="utf-8",
    )
    tickets = check_ticket_dag.load_tickets(tmp_path)
    failures = check_ticket_dag.validate_prefactors(tickets)
    assert any("no ticket file" in f for f in failures)


def test_reserved_and_delegated_decisions_are_reported() -> None:
    ok, msgs = spec_gate.check_decision_record("## Implementation Decisions\n")
    assert ok
    assert sum(m.startswith("warn:") for m in msgs) == 2

    body = (
        "**Reserved decisions:** version\n**Delegated decisions:** file names\n"
    )
    ok, msgs = spec_gate.check_decision_record(body)
    assert ok and any(m.startswith("ok:") for m in msgs)


def test_feature_flag_required_for_user_visible_ship() -> None:
    ok, msgs = spec_gate.check_feature_flag("**Surface:** user-visible\n")
    assert not ok and "Feature flag" in msgs[0]

    ok, msgs = spec_gate.check_feature_flag(
        "**Surface:** user-visible\n**Feature flag:** checkout_v2 (off by default)\n"
    )
    assert ok

    ok, _ = spec_gate.check_feature_flag("**Surface:** internal\n")
    assert ok


def test_door_tiers_and_templates_are_wired() -> None:
    review = (ROOT / "skills/pr_review/SKILL.md").read_text(encoding="utf-8")
    template = (ROOT / "templates/PR_DRAFT.md").read_text(encoding="utf-8")
    spec_t = (ROOT / "skills/spec/references/spec-template.md").read_text(encoding="utf-8")

    assert "two-way" in review and "one-way" in review
    assert "human sign-off" in review or "human sign" in review
    assert "**Feature flag:**" in template
    assert "**Prototype verdict:**" in template
    assert "**Reserved decisions:**" in spec_t
    assert "**Delegated decisions:**" in spec_t
