#!/usr/bin/env python3
"""Frozen evals for agent-config (skills / AGENTS / gates) — no LLM judge.

  python3 scripts/run_agent_config_evals.py --root .
"""
from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import check_edit_guard as eg  # noqa: E402
import check_stale_agent_config as sac  # noqa: E402


def run_evals(harness: Path) -> tuple[bool, list[str]]:
    msgs: list[str] = []
    failed = False

    def rec(name: str, ok: bool, detail: str = "") -> None:
        nonlocal failed
        if ok:
            msgs.append(f"ok: eval `{name}` {detail}".rstrip())
        else:
            failed = True
            msgs.append(f"fail: eval `{name}` {detail}".rstrip())

    ok, m = sac.check(harness)
    rec("stale_clean", ok, m[0] if m else "")

    with tempfile.TemporaryDirectory() as tmp:
        td = Path(tmp)
        (td / "scripts").mkdir()
        (td / "scripts" / "next_skill.py").write_text("#\n", encoding="utf-8")
        (td / "AGENTS.md").write_text("`scripts/nope_missing.py`\n", encoding="utf-8")
        bad_ok, _ = sac.check(td)
        rec("stale_missing", not bad_ok)

    with mock.patch.object(eg, "_diff_names", return_value=[".env"]):
        g_ok, _ = eg.check(harness, fix_task=False)
    rec("edit_guard_env", not g_ok)

    from agent_eval_checklist import evaluate as _ev  # type: ignore

    ev = _ev(harness, run_tests=False)
    rec("checklist", ev.ok)

    return (not failed), msgs


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path("."))
    args = ap.parse_args(argv)
    ok, msgs = run_evals(args.root.resolve())
    for m in msgs:
        print(("✅ " if m.startswith("ok:") else "❌ ") + m)
    print("✅ agent_config_evals ok" if ok else "❌ agent_config_evals FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
