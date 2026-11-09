"""Tests for the completion writer: CLI (vault_done) + writer (vault_writer).

Every acceptance criterion in the spec has a test here. A7/A9 are file- and
environment-level (systemd unit text, vault autocommit) and are marked as such.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import vault_done  # noqa: E402
import vault_writer  # noqa: E402

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
WATCHER = re.compile(r"=== DONE [A-Z0-9-]+ (PASS|FAIL|PARTIAL|DONE|BLOCKED|BLOCKED-needs-CEO) ===")


@pytest.fixture()
def env(tmp_path, monkeypatch):
    state = tmp_path / "state"
    vault = tmp_path / "vault"
    (vault / "agent-tasks").mkdir(parents=True)
    monkeypatch.setenv("HERMES_STATE_DIR", str(state))
    monkeypatch.setenv("HERMES_VAULT_ROOT", str(vault))
    monkeypatch.setenv("HERMES_VAULT_STAGING", "1")
    return {"state": state, "vault": vault, "runs": vault / "agent-tasks" / "hermes-runs" / "_staging"}


def run_cli(*args, capsys=None):
    code = vault_done.main(list(args))
    out = capsys.readouterr() if capsys else None
    return code, out


# ---------------------------------------------------------------- A1/A2/A6: CLI

def test_a1_partial_writes_event_and_prints_matchable_tag(env, capsys):
    code, out = run_cli("--id", "JOB-PARTIAL-1", "--verdict", "PARTIAL", "--needs-ceo",
                        "--detail", "two of three done", capsys=capsys)
    assert code == 0
    assert WATCHER.search(out.out), out.out
    event = json.loads((env["state"] / "spool" / "JOB-PARTIAL-1.json").read_text())
    assert event["verdict"] == "PARTIAL" and event["needs_ceo"] is True


def test_a2_unknown_verdict_writes_nothing(env, capsys):
    code, _ = run_cli("--id", "JOB-BAD-1", "--verdict", "LGTM", capsys=capsys)
    assert code == 2
    assert not (env["state"] / "spool").exists() or not list((env["state"] / "spool").glob("*.json"))


def test_a6_bad_run_id_and_separator_are_refused(env, capsys):
    assert run_cli("--id", "BAD/../ID", "--verdict", "PASS", capsys=capsys)[0] == 2
    assert run_cli("--id", "JOB-OK-1", "--verdict", "PASS", "--detail", "x---y", capsys=capsys)[0] == 2
    assert not list((env["state"] / "spool").glob("*.json")) if (env["state"] / "spool").exists() else True


def test_cli_rejects_newline_and_control_chars(env, capsys):
    assert run_cli("--id", "JOB-NL-1", "--verdict", "PASS", "--detail", "a\nb", capsys=capsys)[0] == 2
    assert run_cli("--id", "JOB-CTL-1", "--verdict", "PASS", "--detail", "a\x07b", capsys=capsys)[0] == 2


# ------------------------------------------------------------------- A3: note

def test_a3_drain_writes_note_and_read_only_processed_copy(env, capsys):
    run_cli("--id", "JOB-PASS-1", "--verdict", "PASS", "--detail", "done", capsys=capsys)
    assert vault_writer.drain() == 0

    notes = list(env["runs"].rglob("JOB-PASS-1.md"))
    assert len(notes) == 1
    text = notes[0].read_text()
    for key in ("run_id:", "verdict:", "needs_ceo:", "content_sha256:", "evidence_sha256:"):
        assert key in text
    processed = env["state"] / "processed" / "JOB-PASS-1.json"
    assert processed.exists()
    assert oct(processed.stat().st_mode)[-3:] == "444"
    assert not (env["state"] / "spool" / "JOB-PASS-1.json").exists()


def test_index_is_rebuilt_not_appended(env, capsys):
    for i in range(3):
        run_cli("--id", f"JOB-IDX-{i}", "--verdict", "PASS", capsys=capsys)
    vault_writer.drain()
    day = next(p for p in env["runs"].iterdir() if p.is_dir())
    index = (day / "INDEX.md").read_text()
    assert index.count("JOB-IDX-") == 3          # one line per run, no duplicates
    vault_writer.drain()                          # nothing to do
    assert (day / "INDEX.md").read_text() == index


# ------------------------------------------------------------- A4: idempotence

def test_a4_same_event_twice_makes_one_note(env, capsys):
    run_cli("--id", "JOB-DUP-1", "--verdict", "PASS", capsys=capsys)
    vault_writer.drain()
    run_cli("--id", "JOB-DUP-1", "--verdict", "PASS", capsys=capsys)   # identical content
    vault_writer.drain()
    assert len(list(env["runs"].rglob("JOB-DUP-1*.md"))) == 1


def test_a4_changed_content_makes_rev2_and_preserves_original(env, capsys):
    run_cli("--id", "JOB-REV-1", "--verdict", "PASS", "--detail", "first", capsys=capsys)
    vault_writer.drain()
    original = next(env["runs"].rglob("JOB-REV-1.md"))
    before = original.read_bytes()

    run_cli("--id", "JOB-REV-1", "--verdict", "PASS", "--detail", "second", capsys=capsys)
    vault_writer.drain()

    assert next(env["runs"].rglob("JOB-REV-1.md")).read_bytes() == before   # untouched
    rev2 = list(env["runs"].rglob("JOB-REV-1--rev2.md"))
    assert len(rev2) == 1


# --------------------------------------------------------------- A5: resume

def test_a5_crash_between_note_and_processed_resumes(env, capsys):
    run_cli("--id", "JOB-CRASH-1", "--verdict", "PASS", "--detail", "x", capsys=capsys)

    real_process = vault_writer.process
    calls = {"n": 0}

    def crash_once(event_path, processed):
        calls["n"] += 1
        if calls["n"] == 1:
            # write the note, then die before the processed copy and unlink
            event = json.loads(event_path.read_text())
            target = vault_writer.note_path(event)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(vault_writer.render_note(event), encoding="utf-8")
            raise OSError("simulated crash after note write")
        return real_process(event_path, processed)

    vault_writer.process = crash_once
    try:
        assert vault_writer.drain() == 5          # first pass fails loudly
    finally:
        vault_writer.process = real_process

    assert (env["state"] / "spool" / "JOB-CRASH-1.json").exists()   # event still queued
    assert vault_writer.drain() == 0                                 # next activation completes
    assert not (env["state"] / "spool" / "JOB-CRASH-1.json").exists()
    assert (env["state"] / "processed" / "JOB-CRASH-1.json").exists()
    assert len(list(env["runs"].rglob("JOB-CRASH-1*.md"))) == 1


# ------------------------------------------------- S1/S2: rendering security

S1_FIXTURE = "<script>alert(1)</script>\n```dataviewjs\ndv.paragraph(\"x\")\n```\n~~~dataviewjs\n~~~~\n`= this.file.name`"


def test_s1_body_is_inert(env, capsys):
    run_cli("--id", "JOB-XSS-1", "--verdict", "PASS", "--detail", S1_FIXTURE.replace("\n", " "),
            capsys=capsys)
    vault_writer.drain()
    note = next(env["runs"].rglob("JOB-XSS-1.md"))
    body = note.read_text().split("---", 2)[2]
    assert "<script" not in body
    assert "```" not in body and "`" not in body
    assert not any(line.lstrip().startswith("~~~") for line in body.splitlines())
    assert "&lt;script>" in body


@pytest.mark.parametrize("raw", [
    "plain", "tab\there", "sep\u2028here", "nel\u0085here", "- leading dash",
    "? question", ": colon", "# hash", "trailing ", 'quote " inside', "back\\slash",
])
def test_s2_yaml_quote_roundtrips_and_escapes(raw):
    quoted = vault_writer.yaml_quote(raw)
    assert quoted.startswith('"') and quoted.endswith('"')
    assert quoted[-2] != " " or raw.endswith(" ")   # a space may only be inside the quotes
    assert "\u2028" not in quoted and "\u2029" not in quoted and "\u0085" not in quoted
    assert "\t" not in quoted
    unescaped = quoted[1:-1].replace('\\"', '"').replace("\\\\", "\\") \
        .replace("\\t", "\t").replace("\\u2028", "\u2028").replace("\\u2029", "\u2029") \
        .replace("\\u0085", "\u0085")
    assert unescaped == raw


def test_frontmatter_stays_one_line_per_field(env, capsys):
    run_cli("--id", "JOB-YAML-1", "--verdict", "PASS", "--job", "a\tb", capsys=capsys)
    vault_writer.drain()
    note = next(env["runs"].rglob("JOB-YAML-1.md"))
    front = note.read_text().split("---")[1]
    assert len([ln for ln in front.splitlines() if ln.strip()]) == 12   # one line per field


# ------------------------------------------------------- A7/A9: environment

def test_a7_units_disable_the_start_limiter():
    unit = (SCRIPT_DIR.parent / "deploy" / "systemd" / "hermes-vault-writer.path").read_text()
    assert "DirectoryNotEmpty=" in unit
    service = (SCRIPT_DIR.parent / "deploy" / "systemd" / "hermes-vault-writer.service").read_text()
    assert "StartLimitIntervalSec=0" in service
    assert "Restart=" not in service or "Restart=no" in service


def test_a9_note_is_a_plain_file_the_vault_can_commit(env, capsys):
    run_cli("--id", "JOB-GIT-1", "--verdict", "PASS", capsys=capsys)
    vault_writer.drain()
    note = next(env["runs"].rglob("JOB-GIT-1.md"))
    assert note.is_file() and note.stat().st_size > 100
    assert note.read_text().startswith("---\n")
