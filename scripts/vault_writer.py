#!/usr/bin/env python3
"""Vault writer — turn spooled completion events into durable vault notes.

Triggered by a systemd path unit (DirectoryNotEmpty on the spool). One note per
run under agent-tasks/hermes-runs/<date>/, one index rebuilt per drain, then the
event is copied into processed/ as a new read-only inode and unlinked from the
spool. Resume-not-skip: a re-run completes missing steps, never goes blind.

Exit codes: 0 clean · 4 manual resolution needed · 5 write/drain failure.
"""
from __future__ import annotations

import errno
import fcntl
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

RUN_ID_RE = re.compile(r"^[A-Z0-9-]{1,64}$")
VERDICTS = ("PASS", "FAIL", "PARTIAL", "DONE", "BLOCKED", "BLOCKED-needs-CEO")
MAX_REV = 5


def state_root() -> Path:
    return Path(os.environ.get("HERMES_STATE_DIR") or (Path.home() / "hermes" / "state"))


def vault_root() -> Path:
    return Path(os.environ.get("HERMES_VAULT_ROOT") or "/opt/second-brain/vault")


def runs_dir() -> Path:
    base = vault_root() / "agent-tasks" / "hermes-runs"
    return base / "_staging" if os.environ.get("HERMES_VAULT_STAGING") == "1" else base


# ---------------------------------------------------------------- rendering

def yaml_quote(value: str) -> str:
    """Double-quoted YAML scalar. Escapes what YAML 1.1 would otherwise interpret."""
    out = ['"']
    for ch in str(value):
        if ch == "\\":
            out.append("\\\\")
        elif ch == '"':
            out.append('\\"')
        elif ch in "\n\r":
            out.append("\\n")
        elif ch == "\t":
            out.append("\\t")
        elif ch in ("\u2028", "\u2029", "\u0085"):
            out.append(f"\\u{ord(ch):04x}")
        elif ord(ch) < 0x20 or ord(ch) == 0x7F:
            out.append(f"\\u{ord(ch):04x}")
        else:
            out.append(ch)
    out.append('"')
    return "".join(out)


def body_escape(text: str) -> str:
    """Free text is rendered inert: no tags, no backticks, no tilde fences."""
    return (str(text).replace("&", "&amp;").replace("<", "&lt;")
            .replace("`", "&#96;").replace("~", "&#126;"))


def render_note(event: dict) -> str:
    fields = [
        ("run_id", event["run_id"]),
        ("verdict", event["verdict"]),
        ("needs_ceo", "true" if event.get("needs_ceo") else "false"),
        ("job", event.get("job", "")),
        ("actor", event.get("actor", "")),
        ("ended_at", event.get("ended_at", "")),
        ("content_sha256", event.get("content_sha256", "")),
        ("scorecard_path_at_write", event.get("scorecard_path_at_write", "")),
        ("scorecard_sha256", event.get("scorecard_sha256", "")),
        ("evidence_sha256", event.get("evidence_sha256", "")),
        ("brief_sha256", event.get("brief_sha256", "")),
        ("host", event.get("host", "")),
    ]
    lines = ["---"] + [f"{k}: {yaml_quote(v)}" for k, v in fields] + ["---", ""]
    lines.append(f"# {body_escape(event['run_id'])} — {body_escape(event['verdict'])}")
    lines.append("")
    if event.get("needs_ceo"):
        lines += ["**A decision is needed from the CEO.**", ""]
    if event.get("detail"):
        lines += ["## Detail", "", body_escape(event["detail"]), ""]
    if event.get("scorecard_path_at_write"):
        lines += ["## Evidence", "", f"- scorecard (historical path): {body_escape(event['scorecard_path_at_write'])}", ""]
    return "\n".join(lines)


def note_path(event: dict) -> Path:
    day = str(event.get("ended_at", ""))[:10] or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return runs_dir() / day / f"{event['run_id']}.md"


def rebuild_index(day: Path) -> None:
    """Rebuild the day index once per drain from the notes, never append per event."""
    rows = []
    for note in sorted(day.glob("*.md")):
        if note.name == "INDEX.md":
            continue
        verdict = needs = ""
        for line in note.read_text(encoding="utf-8").splitlines()[1:14]:
            if line.startswith("verdict:"):
                verdict = line.split(":", 1)[1].strip().strip('"')
            elif line.startswith("needs_ceo:"):
                needs = line.split(":", 1)[1].strip().strip('"')
        rows.append(f"- [[{note.stem}]] · {verdict}{' · needs CEO' if needs == 'true' else ''}")
    (day / "INDEX.md").write_text("# Runs — " + day.name + "\n\n" + "\n".join(rows) + "\n", encoding="utf-8")


# ------------------------------------------------------------------- draining

def process(event_path: Path, processed: Path) -> str:
    """Return a short status string; raise for manual resolution."""
    event = json.loads(event_path.read_text(encoding="utf-8"))
    run_id = event.get("run_id") or ""
    if not RUN_ID_RE.match(run_id):
        raise SystemExit(f"bad run id: {run_id!r}")
    if event.get("verdict") not in VERDICTS:
        raise SystemExit(f"bad verdict: {event.get('verdict')!r}")

    target = note_path(event)
    target.parent.mkdir(parents=True, exist_ok=True)
    rendered = render_note(event)
    sha = event.get("content_sha256", "")

    if target.exists():
        existing = target.read_text(encoding="utf-8")
        if sha and f"content_sha256: \"{sha}\"" in existing:
            status = "resume"                      # complete the missing steps only
        else:
            n = 2
            while (target.with_name(f"{run_id}--rev{n}.md")).exists():
                n += 1
            if n > MAX_REV:
                raise SystemExit(f"{run_id}: more than {MAX_REV} revisions, manual resolution needed")
            target = target.with_name(f"{run_id}--rev{n}.md")
            rendered = rendered.replace("run_id: ", f"supersedes: {yaml_quote('previous')}\nrun_id: ", 1)
            status = f"rev{n}"
    else:
        status = "written"

    if not target.exists() or status.startswith("rev"):
        tmp = target.with_suffix(".md.tmp")
        with tmp.open("w", encoding="utf-8") as fh:
            fh.write(rendered)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, target)

    rebuild_index(target.parent)

    done = processed / event_path.name
    if not done.exists():
        fd = os.open(done, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o444)
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(event_path.read_text(encoding="utf-8"))
            fh.flush()
            os.fsync(fh.fileno())
        os.chmod(done, 0o444)
    os.unlink(event_path)
    return status


def drain(stdout=sys.stdout) -> int:
    spool = state_root() / "spool"
    processed = state_root() / "processed"
    processed.mkdir(parents=True, exist_ok=True)
    spool.mkdir(parents=True, exist_ok=True)

    lock_path = spool / ".lock"
    with lock_path.open("a+") as lock:
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            if exc.errno in (errno.EACCES, errno.EAGAIN):
                print("vault-writer: another drain holds the lock", file=stdout)
                return 0
            raise

        events = sorted(spool.glob("*.json"), key=lambda p: p.stat().st_mtime)
        for event_path in events:
            try:
                status = process(event_path, processed)
            except SystemExit as exc:
                print(f"vault-writer: drain failed stage=render run_id={event_path.stem} exit=4 ({exc})", file=stdout)
                return 4
            except OSError as exc:
                print(f"vault-writer: drain failed stage=write run_id={event_path.stem} exit=5 ({exc})", file=stdout)
                return 5
            print(f"vault-writer: {event_path.stem} {status}", file=stdout)
        if not events:
            print("vault-writer: spool empty", file=stdout)
    return 0


def main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(prog="vault-writer")
    ap.add_argument("--drain", action="store_true", help="process every spooled event")
    ap.add_argument("--status", action="store_true", help="print spool depth")
    args = ap.parse_args(argv)
    if args.status:
        spool = state_root() / "spool"
        print(f"spool: {len(list(spool.glob('*.json')))} event(s) pending")
        return 0
    return drain()


if __name__ == "__main__":
    raise SystemExit(main())
