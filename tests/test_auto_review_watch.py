"""Slice 3 tests for the tmux watcher (harnesses without a hook).

Pane lists come from a JSON fixture through AUTO_REVIEW_TMUX_FIXTURE, so no
test touches a live tmux session or sends anything.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "deploy" / "auto-review-relay.py"
T0 = "2026-11-27T06:00:00Z"

CARD = (
    "  Confirm HEAD and dirty state of both harness trees\n"
    "\n"
    "  1 Yes, proceed\n"
    "  2 No, and tell Grok what to do differently\n"
    "\n"
    "  2/3:select\n"
)


def write_panes(tmp_path: Path, panes: list[dict]) -> Path:
    path = tmp_path / "panes.json"
    path.write_text(json.dumps({"panes": panes}), encoding="utf-8")
    return path


def pane(command: str = "hermes", text: str = CARD, window_name: str = "email-detach",
         pane_id: str = "%5", window: str = "5") -> dict:
    return {
        "pane_id": pane_id,
        "session": "grok-build",
        "window": window,
        "window_name": window_name,
        "command": command,
        "text": text,
    }


def run_watch(tmp_path: Path, panes_file: Path) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["AUTO_REVIEW_STATE"] = str(tmp_path / "state")
    env["AUTO_REVIEW_TMUX_FIXTURE"] = str(panes_file)
    env.pop("AUTO_REVIEW_PANE_LABEL", None)
    env.pop("TMUX_PANE", None)
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--watch", "--once", "--dry", "--now", T0],
        capture_output=True, text=True, timeout=30, env=env,
    )


def signals(out: str) -> list[str]:
    return [line for line in out.splitlines() if line.startswith("SIGNAL: ")]


def test_detects_card_in_agent_pane(tmp_path: Path) -> None:
    proc = run_watch(tmp_path, write_panes(tmp_path, [pane()]))
    assert proc.returncode == 0
    lines = signals(proc.stdout)
    assert len(lines) == 1
    assert "grok-build:5 hermes - approval needed: Confirm HEAD" in lines[0]


def test_second_pass_dedupes(tmp_path: Path) -> None:
    panes_file = write_panes(tmp_path, [pane()])
    first = run_watch(tmp_path, panes_file)
    second = run_watch(tmp_path, panes_file)
    assert len(signals(first.stdout)) == 1
    assert signals(second.stdout) == []
    log = (tmp_path / "state" / "relay.log").read_text()
    assert "watch dedupe" in log


def test_skips_hooked_shell_and_viewer_panes(tmp_path: Path) -> None:
    panes = [
        pane(command="grok", pane_id="%1", window="1"),
        pane(command="bash", pane_id="%2", window="2"),
        pane(command="herdr", pane_id="%3", window="3"),
        pane(command="hermes", window_name="herdr", pane_id="%4", window="4"),
    ]
    proc = run_watch(tmp_path, write_panes(tmp_path, panes))
    assert signals(proc.stdout) == []


def test_detects_yes_no_prompt(tmp_path: Path) -> None:
    text = (
        "  Allow this command to run?\n"
        "\n"
        "  git push origin main\n"
        "\n"
        "  [y/N]\n"
    )
    proc = run_watch(tmp_path, write_panes(tmp_path, [pane(text=text)]))
    lines = signals(proc.stdout)
    assert len(lines) == 1
    assert "Allow this command" in lines[0]


def test_prose_with_no_option_block_is_ignored(tmp_path: Path) -> None:
    text = (
        "No problems found in the last run.\n"
        "Everything is up to date.\n"
    )
    proc = run_watch(tmp_path, write_panes(tmp_path, [pane(text=text)]))
    assert signals(proc.stdout) == []


def test_resolved_card_clears_then_a_new_card_reports(tmp_path: Path) -> None:
    with_card = tmp_path / "with_card.json"
    with_card.write_text(json.dumps({"panes": [pane()]}), encoding="utf-8")
    without = tmp_path / "without_card.json"
    without.write_text(json.dumps({"panes": [pane(text="quiet, no prompt here\n")]}),
                       encoding="utf-8")

    first = run_watch(tmp_path, with_card)
    assert len(signals(first.stdout)) == 1

    resolved = run_watch(tmp_path, without)
    assert signals(resolved.stdout) == []
    state = json.loads((tmp_path / "state" / "state.json").read_text())
    assert state["rows"] == {}

    again = run_watch(tmp_path, with_card)
    assert len(signals(again.stdout)) == 1


def test_title_redacts_tokens_and_paths(tmp_path: Path) -> None:
    text = (
        "  Approve sk-abcdefghijklmnopqrstuv for /home/debian/secret/notes.txt\n"
        "\n"
        "  1 Yes, proceed\n"
        "  2 No\n"
    )
    proc = run_watch(tmp_path, write_panes(tmp_path, [pane(text=text)]))
    out = proc.stdout
    assert "sk-abcdefghijklmnop" not in out
    assert "/home/debian" not in out
    assert "notes.txt" in out


def test_card_at_top_of_pane_still_reports(tmp_path: Path) -> None:
    text = "  1 Yes, proceed\n  2 No\n"
    proc = run_watch(tmp_path, write_panes(tmp_path, [pane(text=text)]))
    assert len(signals(proc.stdout)) == 1


def test_detects_claude_and_codex_fixture_cards(tmp_path: Path) -> None:
    fixtures = REPO / "tests" / "fixtures" / "auto_review"
    claude_text = (fixtures / "claude_card.txt").read_text(encoding="utf-8")
    codex_text = (fixtures / "codex_card.txt").read_text(encoding="utf-8")
    panes = [
        pane(command="claude", text=claude_text, pane_id="%6", window="6", window_name="claude"),
        pane(command="codex", text=codex_text, pane_id="%7", window="7", window_name="codex"),
    ]
    proc = run_watch(tmp_path, write_panes(tmp_path, panes))
    assert proc.returncode == 0
    lines = signals(proc.stdout)
    assert len(lines) == 2
    assert any("grok-build:6 claude - approval needed:" in line for line in lines), lines
    assert any("grok-build:7 codex - approval needed:" in line for line in lines), lines
