#!/usr/bin/env python3
"""Auto-review relay (slice 1): turn a harness approval card into one Signal line
and one Boss POST.

Why: a pane that raises an Auto-review card stops and waits. The end-of-job
scorecard hook fires only on end tags, so a blocked job is invisible until
someone looks at the pane.

Slice 1 covers the core: hook ingest, normalisation, redaction, dedupe, the
hourly cap, message rendering, dry/real delivery, and the reminder sweep.
The tmux watcher, hook wrappers and systemd units are later slices.

Entry points::

    auto-review-relay.py --hook --harness grok      # JSON on stdin
    auto-review-relay.py --sweep                    # 10-minute reminders

Every path fails quiet: a broken relay logs and exits 0, so it can never block
the agent that invoked it.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import TextIO

HERMES_BIN = os.environ.get("AUTO_REVIEW_HERMES_BIN", "/home/debian/.local/bin/hermes")
HERMES_HOME = os.environ.get(
    "AUTO_REVIEW_HERMES_HOME", "/home/debian/hermes/profiles/chief-of-staff"
)
SIGNAL_TARGET = os.environ.get("AUTO_REVIEW_SIGNAL_TARGET", "signal")
BOSS_POSTER = os.environ.get(
    "AUTO_REVIEW_BOSS_POSTER", "/usr/local/lib/pilot/boss_webhook_post.py"
)
WEBHOOK_URL_FILE = "/var/lib/pilot/secrets/sot-ready-webhook.url"
WEBHOOK_KEY_FILE = "/var/lib/pilot/secrets/sot-ready-webhook.key"
DEFAULT_STATE = os.environ.get("AUTO_REVIEW_STATE", "/var/lib/pilot/auto-review-relay")

CAP_PER_HOUR = 12
REMIND_AFTER = 600
CLIP = 200
SIGNAL_MAX = 300
KIND = "auto-review-card"

PERMISSION_HINT = re.compile(r"permission|approv|needs your", re.IGNORECASE)

REDACTORS = [
    re.compile(r"\b(?:ghp|gho|ghs)_[A-Za-z0-9_]{20,}"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{12,}"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"\b[A-Fa-f0-9]{32,}\b"),
    re.compile(r"(?i)\b(api[_-]?key|token|secret|password)\s*[=:]\s*\S+"),
]
ABS_PATH = re.compile(r"(?<![\w:/])/(?:[\w.\-]+/)+([\w.\-]+)")


def _now(value: str | None) -> datetime:
    if value:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _state_dir(raw: str | None) -> Path:
    path = Path(raw or DEFAULT_STATE)
    path.mkdir(parents=True, exist_ok=True)
    (path / "posted").mkdir(exist_ok=True)
    return path


def log(state: Path, message: str) -> None:
    line = f"{_iso(datetime.now(timezone.utc))} {message}\n"
    try:
        with (state / "relay.log").open("a", encoding="utf-8") as fh:
            fh.write(line)
    except OSError:
        pass


def _sent_ok(stdout: str) -> bool:
    """hermes send --json prints a payload; accept a success flag when present."""
    try:
        doc = json.loads(stdout)
    except ValueError:
        return True
    if isinstance(doc, dict) and "success" in doc:
        return bool(doc.get("success"))
    return True


def _first(payload: dict, *names: str) -> object:
    for name in names:
        if name in payload and payload[name] not in (None, ""):
            return payload[name]
    return None


def redact(text: object) -> str:
    out = str(text or "").replace("\n", " ").replace("\r", " ").strip()
    for pattern in REDACTORS:
        out = pattern.sub("[redacted]", out)
    out = ABS_PATH.sub(r"\1", out)
    out = re.sub(r"\s{2,}", " ", out)
    return out[:CLIP]


def pane_label(payload: dict) -> str:
    forced = os.environ.get("AUTO_REVIEW_PANE_LABEL")
    if forced:
        return forced
    pane = os.environ.get("TMUX_PANE", "")
    if pane:
        try:
            proc = subprocess.run(
                ["tmux", "display-message", "-p", "-t", pane,
                 "#{session_name}:#{window_index}"],
                capture_output=True, text=True, timeout=5, check=False,
            )
            label = (proc.stdout or "").strip()
            if proc.returncode == 0 and label:
                return label
        except (OSError, subprocess.SubprocessError):
            pass
    cwd = str(payload.get("cwd") or os.getcwd())
    return Path(cwd).name or "unknown"


def normalize(payload: dict, harness: str) -> dict | None:
    """Return a card row, or None when this event is not an approval prompt."""
    ntype = _first(payload, "notification_type", "notificationType", "type")
    message = redact(_first(payload, "message", "title", "summary") or "")
    if ntype is not None:
        if str(ntype).lower() != "permission_prompt":
            return None
    elif not PERMISSION_HINT.search(message):
        return None

    tool = str(_first(payload, "tool_name", "toolName") or "")
    tool_input = payload.get("tool_input") or payload.get("toolInput") or {}
    command = ""
    if isinstance(tool_input, dict):
        raw = tool_input.get("command") or tool_input.get("cmd") or ""
        if not raw:
            raw = (
                tool_input.get("file_path")
                or tool_input.get("path")
                or tool_input.get("pattern")
                or ""
            )
        command = redact(raw)

    title = message or f"{tool or 'tool'} needs approval"
    label = pane_label(payload)
    pane = os.environ.get("TMUX_PANE", "")
    key_src = f"{harness}|{label}|{pane}|{title}|{command}|{tool}"
    return {
        "key": hashlib.sha256(key_src.encode()).hexdigest(),
        "harness": harness,
        "label": label,
        "pane": pane,
        "title": title,
        "tool": tool,
        "command": command,
    }


def render_signal(row: dict) -> str:
    text = f"{row['label']} {row['harness']} - approval needed: {row['title']}"
    if row.get("command"):
        text += f" - {row['tool'] or 'cmd'}: {row['command']}"
    return text[:SIGNAL_MAX]


def webhook_payload(row: dict, dt: datetime) -> dict:
    return {
        "kind": KIND,
        "harness": row["harness"],
        "session": row["label"].split(":")[0],
        "window": row["label"].split(":")[1] if ":" in row["label"] else "",
        "pane": row["pane"],
        "title": row["title"],
        "tool": row["tool"],
        "command": row["command"],
        "at": _iso(dt),
        "needs-CEO": True,
    }


def send_signal(text: str, state: Path, dry: bool) -> bool:
    if dry:
        print(f"SIGNAL: {text}")
        return True
    if not (os.path.isfile(HERMES_BIN) and os.access(HERMES_BIN, os.X_OK)):
        log(state, "signal skip reason=hermes-bin-missing")
        return False
    env = os.environ.copy()
    env["HERMES_HOME"] = HERMES_HOME
    env["TZ"] = "Asia/Shanghai"
    try:
        proc = subprocess.run(
            [HERMES_BIN, "send", "--to", SIGNAL_TARGET, "--json", text],
            capture_output=True, text=True, timeout=90, check=False, env=env,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        log(state, f"signal error={type(exc).__name__}")
        return False
    ok = proc.returncode == 0 and _sent_ok(proc.stdout or "")
    log(state, f"signal ok={int(ok)} rc={proc.returncode}")
    return ok


def send_webhook(row: dict, state: Path, dt: datetime, dry: bool) -> bool:
    body = json.dumps(webhook_payload(row, dt), sort_keys=True)
    if dry:
        print(f"WEBHOOK: {body}")
        return True
    stamp = int(dt.timestamp())
    payload_file = state / f"payload-{row['key'][:12]}-{stamp}.json"
    payload_file.write_text(body + "\n", encoding="utf-8")
    marker = state / "posted" / f"{row['key'][:12]}-{stamp}"
    runner = [sys.executable, BOSS_POSTER] if BOSS_POSTER.endswith(".py") else [BOSS_POSTER]
    cmd = runner + [
        "--marker", str(marker),
        "--kind", KIND,
        "--payload-file", str(payload_file),
        "--url-file", WEBHOOK_URL_FILE,
        "--key-file", WEBHOOK_KEY_FILE,
        "--log", str(state / "relay.log"),
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              timeout=60, check=False)
    except (OSError, subprocess.SubprocessError) as exc:
        log(state, f"webhook error={type(exc).__name__}")
        return False
    log(state, f"webhook rc={proc.returncode}")
    if proc.returncode == 0:
        payload_file.unlink(missing_ok=True)
    return proc.returncode == 0


def load_state(state: Path) -> dict:
    path = state / "state.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and isinstance(data.get("rows"), dict):
            data.setdefault("sends", [])
            return data
    except (OSError, ValueError):
        pass
    return {"rows": {}, "sends": []}


def save_state(state: Path, data: dict) -> None:
    path = state / "state.json"
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


class Lock:
    def __init__(self, state: Path) -> None:
        self.path = state / "state.lock"
        self.fh: TextIO | None = None

    def __enter__(self) -> "Lock":
        self.fh = self.path.open("w", encoding="utf-8")
        fcntl.flock(self.fh.fileno(), fcntl.LOCK_EX)
        return self

    def __exit__(self, *exc: object) -> None:
        if self.fh is not None:
            fcntl.flock(self.fh.fileno(), fcntl.LOCK_UN)
            self.fh.close()


def _capped(data: dict, now_ts: float) -> bool:
    data["sends"] = [s for s in data["sends"] if now_ts - float(s) < 3600]
    return len(data["sends"]) >= CAP_PER_HOUR


def deliver(row: dict, state: Path, dt: datetime, dry: bool) -> bool:
    ok = send_signal(render_signal(row), state, dry)
    ok = send_webhook(row, state, dt, dry) and ok
    return ok


def handle_hook(args: argparse.Namespace, state: Path, dt: datetime) -> int:
    if (state / "DISABLED").exists():
        log(state, "disabled event=hook")
        return 0
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        log(state, "hook skip reason=bad-json")
        return 0
    if not isinstance(payload, dict):
        log(state, "hook skip reason=not-object")
        return 0
    row = normalize(payload, args.harness)
    if row is None:
        return 0

    with Lock(state):
        data = load_state(state)
        now_ts = dt.timestamp()
        if row["key"] in data["rows"]:
            data["rows"][row["key"]]["last_seen"] = now_ts
            save_state(state, data)
            log(state, f"hook dedupe key={row['key'][:12]}")
            return 0
        if _capped(data, now_ts):
            data["sends"].append(now_ts)
            save_state(state, data)
            log(state, f"hook capped key={row['key'][:12]}")
            return 0
        row["first_seen"] = now_ts
        row["last_seen"] = now_ts
        row["reminded"] = False
        data["rows"][row["key"]] = row
        data["sends"].append(now_ts)
        save_state(state, data)

    deliver(row, state, dt, args.dry)
    log(state, f"hook sent key={row['key'][:12]} harness={row['harness']} label={row['label']}")
    return 0


def pane_text(row: dict) -> str | None:
    forced = os.environ.get("AUTO_REVIEW_PANE_TEXT_FILE")
    if forced:
        try:
            return Path(forced).read_text(encoding="utf-8", errors="replace")
        except OSError:
            return None
    pane = row.get("pane") or ""
    if not pane:
        return None
    try:
        proc = subprocess.run(
            ["tmux", "capture-pane", "-p", "-t", pane, "-S", "-30"],
            capture_output=True, text=True, timeout=5, check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout or ""


def still_up(text: str, row: dict) -> bool:
    probe = row["title"][:60].strip()
    if not probe:
        return False
    return probe.casefold() in text.casefold()


def handle_sweep(args: argparse.Namespace, state: Path, dt: datetime) -> int:
    if (state / "DISABLED").exists():
        log(state, "disabled event=sweep")
        return 0
    now_ts = dt.timestamp()
    with Lock(state):
        data = load_state(state)
        changed = False
        for key, row in list(data["rows"].items()):
            if row.get("reminded"):
                continue
            if now_ts - float(row.get("first_seen", now_ts)) < REMIND_AFTER:
                continue
            text = pane_text(row)
            if text is None:
                log(state, f"sweep skip key={key[:12]} reason=no-pane-text")
                continue
            if still_up(text, row):
                if _capped(data, now_ts):
                    row["reminded"] = True
                    log(state, f"sweep capped key={key[:12]}")
                else:
                    row["reminded"] = True
                    data["sends"].append(now_ts)
                    log(state, f"sweep remind key={key[:12]}")
                    deliver(row, state, dt, args.dry)
                changed = True
            else:
                del data["rows"][key]
                log(state, f"sweep resolved key={key[:12]}")
                changed = True
        if changed:
            save_state(state, data)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--hook", action="store_true")
    mode.add_argument("--sweep", action="store_true")
    parser.add_argument("--harness", default="unknown")
    parser.add_argument("--dry", action="store_true")
    parser.add_argument("--now", default=None)
    parser.add_argument("--state", default=None)
    args = parser.parse_args(argv)

    state = _state_dir(args.state)
    dt = _now(args.now)
    try:
        if args.hook:
            return handle_hook(args, state, dt)
        return handle_sweep(args, state, dt)
    except Exception as exc:  # noqa: BLE001 - fail quiet: never block the calling agent
        log(state, f"error={type(exc).__name__}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
