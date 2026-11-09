#!/usr/bin/env python3
"""`hermes-done` — write one completion event for the vault writer.

The command an executor calls when a job finishes. It writes a single JSON
event into the spool and echoes the legacy chat tag. It does NOT write the
vault: the writer service does that, as a separate, retryable step.

Exit codes: 0 written · 2 refused input (nothing written) · 3 spool unwritable.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

RUN_ID_RE = re.compile(r"^[A-Z0-9-]{1,64}$")
VERDICTS = ("PASS", "FAIL", "PARTIAL", "DONE", "BLOCKED", "BLOCKED-needs-CEO")
# Agreed refuse set for values that would be ambiguous on a single line or in YAML.
_BAD_CHARS = {c for c in range(0x20) if c != 0x09} | {0x7F}


def state_root() -> Path:
    return Path(os.environ.get("HERMES_STATE_DIR") or (Path.home() / "hermes" / "state"))


def spool_dir() -> Path:
    return state_root() / "spool"


def _refuse(field: str, value: str) -> str | None:
    """Return a reason when the value cannot be written safely, else None."""
    if "\n" in value or "\r" in value:
        return f"{field}: newline not allowed"
    if "---" in value:
        return f"{field}: '---' not allowed"
    for ch in value:
        if ord(ch) in _BAD_CHARS:
            return f"{field}: control character U+{ord(ch):04X} not allowed"
    return None


def canonical(event: dict) -> bytes:
    """Stable bytes for hashing: volatile fields excluded so a retry hashes the same."""
    volatile = {"ended_at", "host", "pane"}
    body = {k: v for k, v in event.items() if k not in volatile}
    return json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def build_event(args: argparse.Namespace) -> dict:
    return {
        "run_id": args.id,
        "verdict": args.verdict,
        "needs_ceo": bool(args.needs_ceo),
        "job": args.job or "",
        "detail": args.detail or "",
        "actor": os.environ.get("HERMES_ACTOR") or "hermes",
        "scorecard_path_at_write": args.scorecard or "",
        "scorecard_sha256": args.scorecard_sha256 or "",
        "evidence_sha256": (args.evidence or "").replace("sha256:", ""),
        "brief_sha256": args.brief_sha256 or "",
        "ended_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "host": os.uname().nodename,
        "pane": os.environ.get("TMUX_PANE") or "",
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="hermes-done")
    ap.add_argument("--id", required=True, help="run id, [A-Z0-9-]{1,64}")
    ap.add_argument("--verdict", required=True, help=" | ".join(VERDICTS))
    ap.add_argument("--needs-ceo", action="store_true")
    ap.add_argument("--job", default="")
    ap.add_argument("--detail", default="")
    ap.add_argument("--scorecard", default="")
    ap.add_argument("--scorecard-sha256", default="")
    ap.add_argument("--evidence", default="", help="sha256:<hex> of the evidence artifact")
    ap.add_argument("--brief-sha256", default="")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    if not RUN_ID_RE.match(args.id):
        print("refused: run id must match ^[A-Z0-9-]{1,64}$", file=sys.stderr)
        return 2
    if args.verdict not in VERDICTS:
        print(f"refused: unknown verdict {args.verdict!r}", file=sys.stderr)
        return 2
    for field, value in (
        ("detail", args.detail), ("job", args.job), ("scorecard", args.scorecard),
        ("evidence", args.evidence), ("brief", args.brief_sha256),
    ):
        reason = _refuse(field, value or "")
        if reason:
            print(f"refused: {reason}", file=sys.stderr)
            return 2

    event = build_event(args)
    event["content_sha256"] = hashlib.sha256(canonical(event)).hexdigest()

    spool = spool_dir()
    try:
        spool.mkdir(parents=True, exist_ok=True)
        tmp = spool / f".{args.id}.tmp"
        with tmp.open("w", encoding="utf-8") as fh:
            json.dump(event, fh, ensure_ascii=False, indent=1)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, spool / f"{args.id}.json")
    except OSError as exc:
        print(f"spool unwritable: {exc}", file=sys.stderr)
        return 3

    if args.json:
        print(json.dumps(event, ensure_ascii=False))
    else:
        print(f"=== DONE {args.id} {args.verdict} ===")
        print(f"event: {spool / (args.id + '.json')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
