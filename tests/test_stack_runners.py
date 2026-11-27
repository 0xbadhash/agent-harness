"""Tests for the stack merger, the parallel ticket runner, and the P2 fixes.

Covers AC-5 from the top-50 completion spec.
"""
from __future__ import annotations

import sys
import threading
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import merge_stack  # noqa: E402
import run_tickets  # noqa: E402
import stack_plan  # noqa: E402


def _tickets(tmp_path: Path) -> Path:
    plan = tmp_path / "tickets"
    plan.mkdir()
    (plan / "01-a.md").write_text(
        "# 01 — a\n\n**Blocked by:** None\n**Status:** ready-for-agent\n", encoding="utf-8"
    )
    (plan / "02-b.md").write_text(
        "# 02 — b\n\n**Blocked by:** None\n**Status:** ready-for-agent\n", encoding="utf-8"
    )
    (plan / "03-c.md").write_text(
        "# 03 — c\n\n**Blocked by:** 01, 02\n**Status:** ready-for-agent\n", encoding="utf-8"
    )
    return plan


def test_ticket_order_follows_layers(tmp_path: Path) -> None:
    plan = stack_plan.build_plan(_tickets(tmp_path))
    assert merge_stack.ticket_order(plan) == ["01", "02", "03"]


def test_check_pr_state() -> None:
    assert merge_stack.check_pr_state(
        {"state": "OPEN", "mergeable": "MERGEABLE", "statusCheckRollup": []}
    )[0]
    ok, detail = merge_stack.check_pr_state(
        {
            "state": "OPEN",
            "mergeable": "MERGEABLE",
            "statusCheckRollup": [{"name": "tests", "conclusion": "FAILURE"}],
        }
    )
    assert not ok and "tests=FAILURE" in detail
    assert not merge_stack.check_pr_state(
        {"state": "OPEN", "mergeable": "CONFLICTING"}
    )[0]
    assert not merge_stack.check_pr_state({"state": "MERGED"})[0]


def test_merge_dry_run_lists_the_order(tmp_path: Path) -> None:
    plan = stack_plan.build_plan(_tickets(tmp_path))
    lines = merge_stack.merge(plan, {"01": "10"}, gh=lambda argv: {}, dry_run=True)
    assert lines == ["would merge 01 (PR 10)", "would merge 02 (PR ?)", "would merge 03 (PR ?)"]


def test_merge_calls_gh_in_order(tmp_path: Path) -> None:
    plan = stack_plan.build_plan(_tickets(tmp_path))
    calls: list[list[str]] = []

    def fake_gh(argv: list[str]) -> dict:
        calls.append(argv)
        if argv[:2] == ["pr", "view"]:
            return {"state": "OPEN", "mergeable": "MERGEABLE", "statusCheckRollup": []}
        return {}

    done = merge_stack.merge(
        plan, {"01": "10", "02": "11", "03": "12"}, gh=fake_gh
    )
    assert done[0] == "merged 01 (PR 10)"
    merges = [c for c in calls if c[:2] == ["pr", "merge"]]
    assert [c[2] for c in merges] == ["10", "11", "12"]


def test_merge_stops_when_a_check_is_red(tmp_path: Path) -> None:
    plan = stack_plan.build_plan(_tickets(tmp_path))

    def fake_gh(argv: list[str]) -> dict:
        if argv[:2] == ["pr", "view"]:
            return {
                "state": "OPEN",
                "mergeable": "MERGEABLE",
                "statusCheckRollup": [{"name": "ci", "conclusion": "FAILURE"}],
            }
        return {}

    with pytest.raises(merge_stack.StackMergeError):
        merge_stack.merge(plan, {"01": "10"}, gh=fake_gh)


def test_merge_requires_a_pr_map_entry(tmp_path: Path) -> None:
    plan = stack_plan.build_plan(_tickets(tmp_path))
    with pytest.raises(merge_stack.StackMergeError):
        merge_stack.merge(plan, {}, gh=lambda argv: {})


def test_run_ticket_set_dry_run(tmp_path: Path) -> None:
    results = run_tickets.run_ticket_set(_tickets(tmp_path), lambda tid, d: "s", dry_run=True)
    assert [r.ticket for r in results] == ["01", "02", "03"]
    assert all(r.ok for r in results)


def test_run_ticket_set_blocks_dependents_after_failure(tmp_path: Path) -> None:
    def runner(tid: str, _directory: Path) -> str:
        if tid == "01":
            raise RuntimeError("boom")
        return f"session-{tid}"

    results = run_tickets.run_ticket_set(_tickets(tmp_path), runner, workers=1)
    by_id = {r.ticket: r for r in results}
    assert not by_id["01"].ok
    assert by_id["02"].ok
    assert not by_id["03"].ok
    assert "dependency" in by_id["03"].detail


def test_run_ticket_set_respects_worker_limit(tmp_path: Path) -> None:
    lock = threading.Lock()
    active = 0
    peak = 0

    def runner(tid: str, _directory: Path) -> str:
        nonlocal active, peak
        with lock:
            active += 1
            peak = max(peak, active)
        time.sleep(0.05)
        with lock:
            active -= 1
        return f"session-{tid}"

    run_tickets.run_ticket_set(_tickets(tmp_path), runner, workers=2)
    assert peak <= 2


def test_cli_dry_run_and_command_requirement(tmp_path: Path) -> None:
    tickets = _tickets(tmp_path)
    assert run_tickets.main(["--tickets", str(tickets), "--dry-run"]) == 0
    assert run_tickets.main(["--tickets", str(tickets)]) == 2


def test_run_records_session_ids(tmp_path: Path) -> None:
    results = [run_tickets.RunResult("01", True, session="abc")]
    run_tickets.record_runs(tmp_path, results)
    log = (tmp_path / ".agents" / "artifacts" / "TICKET_RUNS.jsonl").read_text()
    assert '"session": "abc"' in log


def test_ci_scans_every_ticket_root() -> None:
    ci = (ROOT / ".github/workflows/daytime-gates.yml").read_text(encoding="utf-8")
    assert "find .agents/specs -type d -name tickets" in ci
    assert "check_docs_patterns.py" in ci
