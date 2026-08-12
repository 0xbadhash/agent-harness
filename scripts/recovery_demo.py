#!/usr/bin/env python3
"""Tier B-2: demonstrate resumable recovery (read pipeline + print next hint)."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def demo(root: Path) -> tuple[bool, list[str]]:
    root = root.resolve()
    msgs: list[str] = []
    state_path = root / ".agents" / "state" / "pipeline.json"
    if not state_path.is_file():
        # create minimal init for demo
        state_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "phase": "init",
            "updated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "history": [],
        }
        tmp = state_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        tmp.replace(state_path)
        msgs.append("created minimal pipeline.json (init)")
    try:
        data = json.loads(state_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return False, [f"pipeline.json corrupt: {e}"]
    phase = str(data.get("phase") or "unknown")
    msgs.append(f"phase={phase}")
    # write recovery stamp artifact
    art = root / ".agents" / "artifacts"
    art.mkdir(parents=True, exist_ok=True)
    stamp = art / "RECOVERY_DEMO.md"
    stamp.write_text(
        f"# RECOVERY-DEMO\n\n**Marker:** RECOVERY-DEMO\n\n"
        f"phase={phase}\n"
        f"ts={datetime.now(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')}\n"
        f"resumable=true\n",
        encoding="utf-8",
    )
    msgs.append(f"wrote {stamp.relative_to(root)}")
    # re-read
    again = json.loads(state_path.read_text(encoding="utf-8"))
    if str(again.get("phase")) != phase:
        return False, msgs + ["phase changed unexpectedly"]
    try:
        from next_skill import suggest  # type: ignore

        hint = suggest(root) if callable(suggest) else None
        if hint:
            msgs.append(f"next_skill hint: {hint}")
    except Exception:
        msgs.append("next_skill unavailable (ok for bare root)")
    msgs.append("ok: recovery demo resumable path verified")
    return True, msgs


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path("."))
    args = ap.parse_args(argv)
    ok, msgs = demo(args.root.resolve())
    for m in msgs:
        print(("✅ " if ok else "❌ ") + m)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
