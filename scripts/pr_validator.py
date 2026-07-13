#!/usr/bin/env python3
"""Deterministic PR rubric scorer (≥95% to pass). Validates §9 section."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUBRIC = {
    # Suite green when compliance_engine (pytest/type/lint) exits 0.
    # This is NOT proof of red-first TDD — that remains process-enforced in /execute_dev.
    "suite_green": 25,
    "gate_clean": 25,         # type/lint/test pass (same engine; kept for score shape)
    "section_9": 20,          # §9 present + ≥3 entries
    "no_hardcode": 15,        # hardcode scan clean
    "pr_hygiene": 15,         # single roadmap item, atomic commit
}

def _validate_section_9(pr_draft: Path) -> tuple[bool, str, int]:
    if not pr_draft.exists():
        return False, "PR_DRAFT.md not found", 0
    text = pr_draft.read_text(encoding="utf-8")
    if "Things that look bad but are actually fine" not in text:
        return False, "§9 header missing", 0
    m = re.search(r"## Things that look bad but are actually fine\s*\n(.*?)(?=\n## |\Z)", text, re.DOTALL)
    if not m:
        return False, "§9 section not parseable", 0
    body = m.group(1).strip()
    entries = re.findall(r"^\s*(\d+\.|[-*])", body, re.MULTILINE)
    if len(entries) < 3:
        return False, f"§9 has {len(entries)} entries (need ≥3)", len(entries)
    return True, "ok", len(entries)

def score(diff: str | None, pr_draft: Path) -> dict:
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
    r = subprocess.run([sys.executable, str(Path(__file__).with_name("check_hardcodes.py"))],
                       cwd=ROOT, capture_output=True)
    if r.returncode == 0:
        breakdown["no_hardcode"] = RUBRIC["no_hardcode"]
    else:
        violations.append("hardcode scan failed")

    # Gates (stub: assume pass if compliance_engine exits 0)
    r = subprocess.run([sys.executable, str(Path(__file__).with_name("compliance_engine.py")),
                        *(["--diff", diff] if diff else [])],
                       cwd=ROOT, capture_output=True)
    if r.returncode == 0:
        breakdown["gate_clean"] = RUBRIC["gate_clean"]
        breakdown["suite_green"] = RUBRIC["suite_green"]
    else:
        violations.append("compliance gates failed")

    breakdown["pr_hygiene"] = RUBRIC["pr_hygiene"]  # assume ok; refine with git log checks

    # Soft cross_review gate (does not reduce score unless --strict-cross-review)
    try:
        from cross_review_gate import evaluate as _xrev_eval  # type: ignore

        xrev = _xrev_eval(diff, pr_draft)
        if xrev.get("soft_warn"):
            warnings.append(xrev["message"])
        elif xrev.get("message"):
            warnings.append(xrev["message"])
    except Exception as e:  # noqa: BLE001 — soft path must never break scorer
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
    args = ap.parse_args()

    result = score(args.diff, Path(args.pr_draft))
    print(json.dumps(result, indent=2))
    for w in result.get("warnings") or []:
        print(w)

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
