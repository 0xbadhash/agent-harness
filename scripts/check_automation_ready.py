#!/usr/bin/env python3
"""Automation readiness: the outer loop runs only on a proven inner loop.

Preconditions (all must hold):

- the lint ratchet passes and the suppression rule is clean;
- the correction → check map is complete;
- ``.agents/artifacts/BEHAVIOR_REPORT.md`` carries its marker and ``NEXT_SKILL=``;
- ``.agents/artifacts/coverage.json`` is newer than ``--max-age-hours``;
- a named owner is present (``--owner``, ``AUTOMATION_OWNER``, or a
  ``**Owner:**`` line in ``PR_DRAFT.md``).

``--write`` records ``.agents/artifacts/AUTOMATION_READINESS.md`` with an
``AUTOMATION-READY`` marker and the evidence rows. Scheduled jobs (night shift
autofix) refuse to run unless that artifact passes.

Usage::

  python3 scripts/check_automation_ready.py --root . --owner 0xbadhash --write
  python3 scripts/check_automation_ready.py --root . --require-artifact
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = Path(__file__).resolve().parent
ARTIFACT_REL = Path(".agents") / "artifacts" / "AUTOMATION_READINESS.md"
BEHAVIOR_REL = Path(".agents") / "artifacts" / "BEHAVIOR_REPORT.md"
COVERAGE_REL = Path(".agents") / "artifacts" / "coverage.json"
MARKER = "AUTOMATION-READY"
OWNER_RE = re.compile(r"^\s*\*\*Owner:\*\*\s*(\S.*)$", re.MULTILINE)
PLACEHOLDER = {"", "tbd", "todo", "none", "unknown", "<owner>", "owner"}


def _add_scripts_path() -> None:
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))


def _owner_from_draft(root: Path) -> str:
    draft = root / "PR_DRAFT.md"
    if not draft.is_file():
        return ""
    match = OWNER_RE.search(draft.read_text(encoding="utf-8", errors="replace"))
    return match.group(1).strip() if match else ""


def resolve_owner(root: Path, explicit: str | None = None) -> str:
    for raw in (explicit, os.environ.get("AUTOMATION_OWNER"), _owner_from_draft(root)):
        value = (raw or "").strip()
        if value.lower() not in PLACEHOLDER:
            return value
    return ""


def _coverage_check(root: Path, max_age_hours: float) -> tuple[bool, str]:
    path = root / COVERAGE_REL
    if not path.is_file():
        return False, "fail: coverage.json missing — run pytest with --cov"
    age = datetime.now(UTC) - datetime.fromtimestamp(path.stat().st_mtime, UTC)
    if age > timedelta(hours=max_age_hours):
        return False, (
            f"fail: coverage.json is {age.total_seconds() / 3600:.1f}h old "
            f"(cap {max_age_hours:g}h)"
        )
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return False, f"fail: coverage.json unreadable: {exc}"
    totals = data.get("totals") if isinstance(data, dict) else None
    if not isinstance(totals, dict) or "percent_covered" not in totals:
        return False, "fail: coverage.json has no totals.percent_covered"
    return True, f"ok: coverage {float(totals['percent_covered']):.1f}% fresh"


def _behavior_check(root: Path) -> tuple[bool, str]:
    path = root / BEHAVIOR_REL
    if not path.is_file():
        return False, "fail: BEHAVIOR_REPORT.md missing"
    text = path.read_text(encoding="utf-8", errors="replace")
    if "BEHAVIOR-REPORT" not in text:
        return False, "fail: BEHAVIOR_REPORT.md missing BEHAVIOR-REPORT marker"
    if "NEXT_SKILL=" not in text:
        return False, "fail: BEHAVIOR_REPORT.md missing NEXT_SKILL line"
    return True, "ok: behavior artifact present"


def check(
    root: Path,
    *,
    owner: str | None = None,
    max_age_hours: float = 24.0,
) -> tuple[bool, list[str]]:
    """Return (ok, messages). Fails closed; every failed row is named."""
    _add_scripts_path()
    root = Path(root)
    messages: list[str] = []
    ok = True

    try:
        from check_lint_ratchet import check as lint_check

        lint_ok, lint_msgs = lint_check(root)
    except Exception as exc:  # noqa: BLE001
        lint_ok, lint_msgs = False, [f"lint ratchet unavailable: {exc}"]
    messages.append(("ok: lint ratchet" if lint_ok else "fail: lint ratchet — " + lint_msgs[0]))
    ok = ok and lint_ok

    try:
        from check_type_ignores import check as ignore_check

        ign_ok, ign_msgs = ignore_check(root)
    except Exception as exc:  # noqa: BLE001
        ign_ok, ign_msgs = False, [f"type-ignore check unavailable: {exc}"]
    messages.append(("ok: suppressions" if ign_ok else "fail: suppressions — " + ign_msgs[0]))
    ok = ok and ign_ok

    try:
        from check_correction_checks import check as correction_check

        corr_ok, corr_msgs = correction_check(root)
    except Exception as exc:  # noqa: BLE001
        corr_ok, corr_msgs = False, [f"correction map unavailable: {exc}"]
    messages.append(("ok: corrections mapped" if corr_ok else "fail: corrections — " + corr_msgs[0]))
    ok = ok and corr_ok

    beh_ok, beh_msg = _behavior_check(root)
    messages.append(beh_msg if beh_ok else beh_msg)
    ok = ok and beh_ok

    cov_ok, cov_msg = _coverage_check(root, max_age_hours)
    messages.append(cov_msg)
    ok = ok and cov_ok

    resolved = resolve_owner(root, owner)
    if resolved:
        messages.append(f"ok: owner {resolved}")
    else:
        messages.append(
            "fail: owner missing — pass --owner, set AUTOMATION_OWNER, or add "
            "`**Owner:** <name>` to PR_DRAFT.md"
        )
        ok = False

    if ok:
        messages.append("ok: automation readiness proven")
    return ok, messages


def write_artifact(root: Path, owner: str, messages: list[str]) -> Path:
    root = Path(root)
    path = root / ARTIFACT_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    rows = "\n".join(f"- {m}" for m in messages)
    body = (
        f"# AUTOMATION-READINESS\n\n**Marker:** {MARKER}\n"
        f"**Recorded:** {stamp}\n**Owner:** {owner}\n\n"
        "The outer loop may run only while this artifact passes.\n\n"
        f"## Checks\n\n{rows}\n"
    )
    path.write_text(body, encoding="utf-8")
    return path


def check_artifact(root: Path, *, max_age_hours: float = 24.0) -> tuple[bool, list[str]]:
    """Return (ok, messages) for a scheduled job gating on the artifact."""
    path = Path(root) / ARTIFACT_REL
    if not path.is_file():
        return False, [
            "fail: AUTOMATION_READINESS.md missing — run "
            "check_automation_ready.py --write on a green inner loop"
        ]
    text = path.read_text(encoding="utf-8", errors="replace")
    if MARKER not in text:
        return False, ["fail: AUTOMATION_READINESS.md missing marker"]
    age = datetime.now(UTC) - datetime.fromtimestamp(path.stat().st_mtime, UTC)
    if age > timedelta(hours=max_age_hours):
        return False, [
            f"fail: AUTOMATION_READINESS.md is {age.total_seconds() / 3600:.1f}h old "
            f"(cap {max_age_hours:g}h)"
        ]
    if "fail:" in text:
        return False, ["fail: AUTOMATION_READINESS.md records a failed check"]
    return True, [f"ok: automation readiness artifact current ({age.total_seconds() / 3600:.1f}h)"]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--owner", default=None)
    ap.add_argument("--max-age-hours", type=float, default=24.0)
    ap.add_argument("--write", action="store_true", help="Record the readiness artifact")
    ap.add_argument(
        "--require-artifact",
        action="store_true",
        help="Validate an existing artifact instead of running the checks",
    )
    args = ap.parse_args(argv)
    root = args.root.resolve()

    if args.require_artifact:
        ok, messages = check_artifact(root, max_age_hours=args.max_age_hours)
    else:
        ok, messages = check(root, owner=args.owner, max_age_hours=args.max_age_hours)
        if ok and args.write:
            owner = resolve_owner(root, args.owner)
            path = write_artifact(root, owner, messages)
            messages.append(f"ok: wrote {path.relative_to(root).as_posix()}")
    for message in messages:
        print(("✅ " if ok else "❌ ") + message)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
