#!/usr/bin/env python3
"""Deterministic PR rubric scorer (≥95% to pass). Includes hard gates pack."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

RUBRIC = {
    # Suite green when compliance_engine (pytest/type/lint) exits 0.
    "suite_green": 20,
    "gate_clean": 20,  # type/lint/test pass
    "section_9": 15,  # §9 present + ≥3 entries
    "no_hardcode": 10,
    "pr_hygiene": 10,
    # Fail-closed evidence pack (all applicable gates must pass for full points)
    "hard_gates": 25,
}


def _validate_section_9(pr_draft: Path) -> tuple[bool, str, int]:
    if not pr_draft.exists():
        return False, "PR_DRAFT.md not found", 0
    text = pr_draft.read_text(encoding="utf-8")
    if "Things that look bad but are actually fine" not in text:
        return False, "§9 header missing", 0
    m = re.search(
        r"## Things that look bad but are actually fine\s*\n(.*?)(?=\n## |\Z)",
        text,
        re.DOTALL,
    )
    if not m:
        return False, "§9 section not parseable", 0
    body = m.group(1).strip()
    entries = re.findall(r"^\s*(\d+\.|[-*])", body, re.MULTILINE)
    if len(entries) < 3:
        return False, f"§9 has {len(entries)} entries (need ≥3)", len(entries)
    return True, "ok", len(entries)


def score(
    diff: str | None,
    pr_draft: Path,
    *,
    skip_hard_gates: bool = False,
) -> dict:
    breakdown = {k: 0 for k in RUBRIC}
    violations: list[str] = []
    warnings: list[str] = []

    # §9
    ok, msg, n = _validate_section_9(pr_draft)
    if ok:
        breakdown["section_9"] = RUBRIC["section_9"]
    else:
        violations.append(f"§9: {msg}")

    # Hardcodes
    r = subprocess.run(
        [sys.executable, str(Path(__file__).with_name("check_hardcodes.py"))],
        cwd=ROOT,
        capture_output=True,
    )
    if r.returncode == 0:
        breakdown["no_hardcode"] = RUBRIC["no_hardcode"]
    else:
        violations.append("hardcode scan failed")

    # Compliance gates
    r = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).with_name("compliance_engine.py")),
            *(["--diff", diff] if diff else []),
        ],
        cwd=ROOT,
        capture_output=True,
    )
    if r.returncode == 0:
        breakdown["gate_clean"] = RUBRIC["gate_clean"]
        breakdown["suite_green"] = RUBRIC["suite_green"]
    else:
        violations.append("compliance gates failed")

    # PR hygiene
    hygiene_ok = True
    if not pr_draft.is_file():
        hygiene_ok = False
        violations.append("pr_hygiene: PR_DRAFT.md missing")
    else:
        draft = pr_draft.read_text(encoding="utf-8", errors="replace")
        for needle in (
            "What Problem This Solves",
            "Why This Change Was Made",
            "User Impact",
            "Evidence",
        ):
            if needle not in draft:
                hygiene_ok = False
                violations.append(f"pr_hygiene: PR_DRAFT missing section «{needle}»")
                break
    try:
        log = subprocess.run(
            ["git", "-C", str(ROOT), "rev-list", "--count", "HEAD"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if log.returncode != 0:
            hygiene_ok = False
            violations.append("pr_hygiene: git rev-list failed")
    except (OSError, subprocess.TimeoutExpired):
        pass
    if hygiene_ok:
        breakdown["pr_hygiene"] = RUBRIC["pr_hygiene"]
    else:
        breakdown["pr_hygiene"] = 0

    # Hard gates pack (fail closed)
    try:
        from hard_gates import evaluate as _hg_eval  # type: ignore

        hg = _hg_eval(
            ROOT,
            pr_draft,
            diff=diff,
            skip=skip_hard_gates,
        )
        if hg.ok:
            breakdown["hard_gates"] = RUBRIC["hard_gates"]
        else:
            breakdown["hard_gates"] = 0
            violations.extend(hg.violations)
        for s in hg.skipped:
            warnings.append(f"hard_gates skip: {s}")
    except Exception as e:  # noqa: BLE001
        breakdown["hard_gates"] = 0
        violations.append(f"hard_gates: evaluation error: {e}")

    # Soft cross_review
    try:
        from cross_review_gate import evaluate as _xrev_eval  # type: ignore

        xrev = _xrev_eval(diff, pr_draft)
        if xrev.get("soft_warn"):
            warnings.append(xrev["message"])
        elif xrev.get("message"):
            warnings.append(xrev["message"])
    except Exception as e:  # noqa: BLE001
        warnings.append(f"cross_review soft-gate skipped: {e}")

    total = sum(breakdown.values())
    return {
        "score": total,
        "max": sum(RUBRIC.values()),
        "breakdown": breakdown,
        "violations": violations,
        "warnings": warnings,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--diff", help="Git range")
    ap.add_argument("--pr-draft", default=str(ROOT / "PR_DRAFT.md"))
    ap.add_argument("--write-pr-draft", action="store_true")
    ap.add_argument("--update-pipeline", action="store_true")
    ap.add_argument(
        "--strict-cross-review",
        action="store_true",
        help="Exit 1 if large diff lacks CROSS-REVIEW evidence (hard gate; default soft)",
    )
    ap.add_argument(
        "--skip-hard-gates",
        action="store_true",
        help="Emergency only: requires ALLOW_SKIP_HARD_GATES=1; always logs skip",
    )
    args = ap.parse_args()

    skip_hg = bool(args.skip_hard_gates)
    if skip_hg:
        import os

        if os.environ.get("ALLOW_SKIP_HARD_GATES", "").strip() not in ("1", "true", "yes"):
            print(
                "❌ --skip-hard-gates requires env ALLOW_SKIP_HARD_GATES=1 "
                "(J6 ship bar — silent skip forbidden)",
                file=sys.stderr,
            )
            return 1
        print(
            "⚠️  ALLOW_SKIP_HARD_GATES=1 — hard gates skipped (audit log written)",
            file=sys.stderr,
        )

    result = score(
        args.diff,
        Path(args.pr_draft),
        skip_hard_gates=skip_hg,
    )
    print(json.dumps(result, indent=2))
    for w in result.get("warnings") or []:
        print(w)
    for v in result.get("violations") or []:
        if v.startswith("hard_gates"):
            print(f"❌ {v}")

    if args.strict_cross_review:
        try:
            from cross_review_gate import evaluate as _xrev_eval  # type: ignore

            xrev = _xrev_eval(args.diff, Path(args.pr_draft))
            if xrev.get("soft_warn"):
                print("❌ strict cross_review gate failed")
                if args.update_pipeline:
                    import pipeline_state  # type: ignore

                    pipeline_state.set_phase("blocked", score=result["score"])
                    print(f"✅ pipeline → blocked (score {result['score']})")
                return 1
        except Exception as e:  # noqa: BLE001
            print(f"⚠️ strict cross_review check error: {e}")

    if args.update_pipeline:
        import pipeline_state  # type: ignore

        phase = "approved" if result["score"] >= 95 else "blocked"
        pipeline_state.set_phase(phase, score=result["score"])
        print(f"✅ pipeline → {phase} (score {result['score']})")
    return 0 if result["score"] >= 95 else 1


if __name__ == "__main__":
    sys.exit(main())
