"""Tests for wired helpers, spec rituals, issue flows, and stack layers.

Covers AC-1, AC-2, AC-3, AC-4, and AC-5 from the T2088U spec.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_ac_1_helpers_wired() -> None:
    execute = _read("skills/execute_dev/SKILL.md")
    review = _read("skills/code_review/SKILL.md")
    retro = _read("skills/retrospect/SKILL.md")
    ci = _read(".github/workflows/daytime-gates.yml")

    assert "check_ticket_dag.py" in execute
    assert "smart_zone_guard.py" in execute
    assert "check_compact_safety.py" in execute
    assert "check_comment_audit.py" in review
    assert "retro_job.py" in retro
    assert "check_comment_audit.py" in ci
    assert "check_ticket_dag.py" in ci


def test_ac_2_spec_rituals_and_glossary_collision(tmp_path: Path) -> None:
    grill = _read("skills/spec/references/grill-me-checklist.md")
    clarify = _read("skills/spec/references/clarify-checklist.md")
    skill = _read("skills/spec/SKILL.md")

    assert "STOP" in grill
    assert "why" in grill.lower()
    assert "pain ranking" in grill.lower()
    assert "scenario" in clarify.lower()
    assert "candidate" in clarify.lower()
    assert "STOP" in skill
    assert "pain ranking" in skill.lower()
    assert "scenario" in skill.lower()

    import spec_gate

    glossary = tmp_path / "GLOSSARY.md"
    glossary.write_text(
        "| Term | Definition |\n|---|---|\n| policy_id | id |\n| Policy ID | same |\n",
        encoding="utf-8",
    )
    ok, messages = spec_gate.check_glossary_collisions(tmp_path)
    assert ok is False, messages

    glossary.write_text(
        "| Term | Definition |\n|---|---|\n| policy_id | id |\n| digest | d |\n",
        encoding="utf-8",
    )
    ok_clean, _ = spec_gate.check_glossary_collisions(tmp_path)
    assert ok_clean is True


def test_ac_3_workflow_data_companion() -> None:
    companion = ROOT.parent / "workflow-harness"
    if not companion.is_dir():
        pytest.skip("workflow-harness companion tree is not present")

    data = json.loads((companion / "glossary.json").read_text(encoding="utf-8"))
    assert data["version"] >= 1
    assert len(data["terms"]) >= 6
    for term, entry in data["terms"].items():
        assert entry.get("definition", "").strip(), f"{term} lacks a definition"

    ticket = (companion / "tickets" / "02-ingest-fanout.md").read_text(encoding="utf-8")
    assert "**Blocked by:**" in ticket
    assert "**Status:**" in ticket
    assert ticket.count("- [ ]") >= 3


def test_ac_4_issue_bodies_offline(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import retro_job

    artifacts = tmp_path / ".agents" / "artifacts"
    artifacts.mkdir(parents=True)
    (artifacts / "CODE_REVIEW.md").write_text(
        "- Fix: add a regression test for the parser edge case\n",
        encoding="utf-8",
    )

    calls: list[tuple] = []

    def _no_run(*args, **kwargs):
        calls.append(args)
        raise AssertionError("subprocess.run must not run without --gh")

    monkeypatch.setattr(retro_job.subprocess, "run", _no_run)

    assert retro_job.main(["--root", str(tmp_path), "--file-issues"]) == 0
    issues = sorted((artifacts / "issues").glob("*.md"))
    assert any("umbrella" in path.name for path in issues)
    assert len(issues) >= 2
    umbrella = next(path for path in issues if "umbrella" in path.name)
    assert "Umbrella" in umbrella.read_text(encoding="utf-8")
    assert calls == []

    assert retro_job.main(["--root", str(tmp_path), "--gh"]) != 0

    qa = _read("skills/qa_campaign/SKILL.md")
    assert "--file-issues" in qa


def test_ac_5_stack_plan_layers_and_chunks(tmp_path: Path) -> None:
    import stack_plan

    tickets = tmp_path / "tickets"
    tickets.mkdir()
    (tickets / "01-root.md").write_text(
        "# 01\n\n**Blocked by:** None\n\n**Status:** ready-for-agent\n",
        encoding="utf-8",
    )
    (tickets / "02-second.md").write_text(
        "# 02\n\n**Blocked by:** 01\n\n**Status:** ready-for-agent\n",
        encoding="utf-8",
    )
    (tickets / "03-third.md").write_text(
        "# 03\n\n**Blocked by:** 01, 02\n\n**Status:** ready-for-agent\n",
        encoding="utf-8",
    )

    plan = stack_plan.build_plan(tickets)
    assert plan["layers"] == [["01"], ["02"], ["03"]]
    assert plan["chunks"][0]["tickets"] == ["01"]

    markdown = stack_plan.render_markdown(plan)
    assert "Layer 1" in markdown
    assert "CHUNK 1" in markdown

    assert stack_plan.main(["--tickets", str(tickets), "--root", str(tmp_path), "--write"]) == 0
    assert (tmp_path / ".agents" / "artifacts" / "STACK_PLAN.md").is_file()
    assert (tmp_path / ".agents" / "artifacts" / "STACK_PLAN.json").is_file()

    (tickets / "01-root.md").write_text(
        "# 01\n\n**Blocked by:** 02\n\n**Status:** ready-for-agent\n",
        encoding="utf-8",
    )
    assert stack_plan.main(["--tickets", str(tickets), "--root", str(tmp_path)]) == 1

    execute = _read("skills/execute_dev/SKILL.md")
    review = _read("skills/code_review/SKILL.md")
    assert "stack_plan.py" in execute
    assert "stack_plan.py" in review
