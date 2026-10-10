#!/usr/bin/env python3
"""Deterministic GPA scorer. Rubric only. Never prints trace secrets."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

METRICS = (
    "outcome_correctness",
    "tool_selection",
    "tool_execution",
    "logical_consistency",
    "groundedness",
    "policy_adherence",
)

ROOT = Path(__file__).resolve().parents[1]
RUBRIC = ROOT / "skills" / "gpa_eval" / "references" / "rubric.json"


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, round(value, 4)))


def score_trace(trace: dict, rubric: dict) -> dict:
    actions = list(trace.get("actions") or [])
    plan = list(trace.get("plan") or [])
    policies = list(trace.get("policy_points") or [])
    outcome = str(trace.get("outcome") or "")
    expected = str(trace.get("expected") or "").lower()
    upper = outcome.upper()

    if "FAIL" in upper and "PASS" in upper:
        outcome_correctness = 0.5
    elif "FAIL" in upper or upper.strip() in {"0", "FALSE"}:
        outcome_correctness = 0.0
    elif "PASS" in upper:
        outcome_correctness = 1.0
    else:
        outcome_correctness = 0.0

    if not actions:
        tool_selection = 0.0
        tool_execution = 0.0
    else:
        tool_selection = _clamp(
            sum(1 for a in actions if str(a.get("tool") or "").strip()) / len(actions)
        )
        tool_execution = _clamp(
            sum(1 for a in actions if a.get("ok") is True) / len(actions)
        )

    live_required = "live" in expected
    standalone = any(
        "standalone" in str(step.get("step") or "").lower() for step in plan
    )
    logical_consistency = 0.0 if live_required and standalone else 1.0

    evidence_bits = 0
    evidence_total = max(1, len(actions) + len(policies))
    for action in actions:
        if str(action.get("result_summary") or "").strip():
            evidence_bits += 1
    for point in policies:
        if str(point.get("evidence") or "").strip():
            evidence_bits += 1
    groundedness = _clamp(evidence_bits / evidence_total)

    if not policies:
        policy_adherence = 0.0
    else:
        policy_adherence = _clamp(
            sum(1 for p in policies if p.get("honoured") is True) / len(policies)
        )

    scores = {
        "outcome_correctness": outcome_correctness,
        "tool_selection": tool_selection,
        "tool_execution": tool_execution,
        "logical_consistency": logical_consistency,
        "groundedness": groundedness,
        "policy_adherence": policy_adherence,
    }

    failed_policy = next((p for p in policies if p.get("honoured") is not True), None)
    bad_step = next(
        (
            step
            for step in plan
            if live_required and "standalone" in str(step.get("step") or "").lower()
        ),
        None,
    )
    if bad_step is not None:
        step_index = int(bad_step.get("index", 0))
        why = "plan step builds a standalone surface while expected requires the live page"
        weakest = "logical_consistency"
    elif failed_policy is not None:
        step_index = 0
        why = f"policy not honoured: {failed_policy.get('rule')}"
        weakest = "policy_adherence"
    else:
        weakest = min(METRICS, key=lambda name: scores[name])
        step_index = 0
        why = f"lowest metric {weakest}"

    suggestions = rubric.get("suggestions") or {}
    suggestion = suggestions.get(weakest) or suggestions.get("none") or ""

    return {
        "judge": "rubric",
        "llm_judge": False,
        "scores": scores,
        "error_localization": {"step_index": step_index, "why": why},
        "suggestion": suggestion,
        "scorecard_path": trace.get("scorecard_path") or "",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Score one GPA trace")
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--rubric", type=Path, default=RUBRIC)
    args = parser.parse_args(argv)
    trace = json.loads(args.trace.read_text(encoding="utf-8"))
    rubric = json.loads(args.rubric.read_text(encoding="utf-8"))
    result = score_trace(trace, rubric)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        "gpa_eval",
        " ".join(f"{name}={result['scores'][name]}" for name in METRICS),
        f"step={result['error_localization']['step_index']}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
