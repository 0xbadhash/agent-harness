"""GPA rubric: six scores, one localization, one suggestion."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from gpa_eval import METRICS, score_trace  # noqa: E402

RUBRIC = json.loads(
    (ROOT / ".agents/skills/gpa_eval/references/rubric.json").read_text(encoding="utf-8")
)


def _trace():
    return {
        "goal": "Cyclic motion on the live Catalyxt homepage",
        "expected": "Motion loop passes and the layout matches the live page",
        "plan": [
            {"index": 0, "step": "Build a standalone HyperFrames card"},
            {"index": 1, "step": "Record the loop"},
        ],
        "actions": [
            {
                "index": 0,
                "tool": "write_preview",
                "args_redacted": "preview index.html",
                "result_summary": "standalone card served",
                "ok": True,
            },
            {
                "index": 1,
                "tool": "measure_loop",
                "args_redacted": "performance.now",
                "result_summary": "delta 0 at 8001 and 24001",
                "ok": True,
            },
        ],
        "outcome": "motion PASS, layout FAIL against live",
        "policy_points": [
            {
                "rule": "build inside live page",
                "honoured": False,
                "evidence": "R2 redid the preview as the live homepage",
            }
        ],
        "scorecard_path": "agent-tasks/evidence/SCORECARD-W4-CATALYXT-CYCLIC-MOTION-2026-10-10.md",
    }


def test_r1_localizes_standalone_plan_step():
    result = score_trace(_trace(), RUBRIC)
    assert list(result["scores"]) == list(METRICS)
    assert all(0.0 <= result["scores"][name] <= 1.0 for name in METRICS)
    assert result["scores"]["outcome_correctness"] == 0.5
    assert result["scores"]["logical_consistency"] == 0.0
    assert result["scores"]["policy_adherence"] == 0.0
    assert result["error_localization"]["step_index"] == 0
    assert "standalone" in result["error_localization"]["why"]
    assert result["suggestion"].count(".") >= 1
    assert result["llm_judge"] is False
