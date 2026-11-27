"""Tests for comment policy, JS lint ratchet, session cost, repro, and docs patterns.

Covers AC-3 from the top-50 completion spec.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import check_comment_audit  # noqa: E402
import check_docs_patterns  # noqa: E402
import session_context  # noqa: E402
import spec_gate  # noqa: E402
import stack_plan  # noqa: E402


def test_comment_ratio_counts_only_comments_and_code() -> None:
    comments, code = check_comment_audit.comment_counts(
        "# why\n\nx = 1\n# also why\ny = 2\n"
    )
    assert (comments, code) == (2, 2)


def test_comment_policy_and_skill_exist() -> None:
    policy = (ROOT / ".agents/policy/comment-policy.md").read_text(encoding="utf-8")
    skill = (ROOT / "skills/comment_audit/SKILL.md").read_text(encoding="utf-8")
    review = (ROOT / "skills/code_review/SKILL.md").read_text(encoding="utf-8")
    assert "Phase 1" in policy and "--ratio" in policy
    assert "check_comment_audit.py" in skill
    assert "--ratio" in review


def test_rejected_pattern_flags_a_teaching_line(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "bad.md").write_text("Run with --yolo to skip gates.\n", encoding="utf-8")
    ok, findings = check_docs_patterns.check(tmp_path)
    assert not ok and "yolo-flag" in findings[0]


def test_rejected_pattern_allows_a_retired_note(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "ok.md").write_text(
        "`--yolo` is retired; use the phase FSM.\n", encoding="utf-8"
    )
    ok, findings = check_docs_patterns.check(tmp_path)
    assert ok, findings


def test_rejected_pattern_skips_historical_specs(tmp_path: Path) -> None:
    (tmp_path / "docs" / "specs").mkdir(parents=True)
    (tmp_path / "docs" / "specs" / "old.md").write_text("--yolo was removed.\n", encoding="utf-8")
    ok, findings = check_docs_patterns.check(tmp_path)
    assert ok, findings


def test_repo_docs_are_clean() -> None:
    ok, findings = check_docs_patterns.check(ROOT)
    assert ok, findings


def test_js_lint_ratchet_template_is_complete() -> None:
    base = ROOT / "templates/eslint-ratchet"
    assert (base / "eslint.config.mjs").is_file()
    assert (base / "baseline.json").is_file()
    assert (base / "eslint-ratchet.mjs").is_file()
    tdd = (ROOT / "docs/tdd.md").read_text(encoding="utf-8")
    assert "Constraints belong in test names" in tdd


def test_session_cost_is_unknown_until_recorded(tmp_path: Path) -> None:
    ctx = session_context.build(tmp_path)
    assert ctx.tokens == "unknown"
    assert ctx.cost_source == "not-recorded"

    path = tmp_path / ".agents" / "artifacts" / "session_cost.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"tokens": 1000, "context_tokens": 400, "cost_usd": 0.5}), encoding="utf-8")
    ctx = session_context.build(tmp_path)
    assert ctx.tokens == "1000"
    assert ctx.context_tokens == "400"
    assert ctx.cost_usd == "0.5"
    assert ctx.cost_source == "session_cost.json"


def test_session_cost_markdown_is_written(tmp_path: Path) -> None:
    assert session_context.main(["--root", str(tmp_path), "--write"]) == 0
    out = tmp_path / ".agents" / "artifacts" / "SESSION_COST.md"
    text = out.read_text(encoding="utf-8")
    assert "| tokens | `unknown` |" in text


def test_handoff_threshold_is_documented() -> None:
    handoff = (ROOT / "skills/handoff/SKILL.md").read_text(encoding="utf-8")
    execute = (ROOT / "skills/execute_dev/SKILL.md").read_text(encoding="utf-8")
    assert "120,000 context tokens" in handoff
    assert "session_context.py" in execute
    assert "hand off" in execute.lower()


def test_repro_cmd_required_for_a_defect_fix() -> None:
    ok, msgs = spec_gate.check_repro_cmd("**Kind:** fix\nred_cmd: pytest\n")
    assert not ok and "repro_cmd" in msgs[0]

    ok, msgs = spec_gate.check_repro_cmd(
        "**Kind:** fix\nrepro_cmd: curl -s localhost:8000/x\n"
    )
    assert ok


def test_process_lens_is_in_cross_review() -> None:
    review = (ROOT / "skills/cross_review/SKILL.md").read_text(encoding="utf-8")
    assert "Process lens" in review
    assert "session_context.py" in review


def test_stack_plan_default_estimate_is_configurable(tmp_path: Path) -> None:
    (tmp_path / "01-a.md").write_text(
        "# 01 — a\n\n**Blocked by:** None\n**Status:** ready-for-agent\n",
        encoding="utf-8",
    )
    plan = stack_plan.build_plan(tmp_path, default_estimate=42)
    assert plan["estimates"]["01"] == 42

    (tmp_path / "02-b.md").write_text(
        "# 02 — b\n\n**Blocked by:** 01\n**Estimate:** 90\n", encoding="utf-8"
    )
    plan = stack_plan.build_plan(tmp_path, default_estimate=42)
    assert plan["estimates"] == {"01": 42, "02": 90}
