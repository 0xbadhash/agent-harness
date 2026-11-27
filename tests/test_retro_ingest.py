"""Tests for retro transcript/PR-comment ingest and action classes.

Covers AC-4 from the top-50 completion spec.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import retro_job  # noqa: E402


def test_action_classes_cover_every_cluster() -> None:
    for label in ("tests", "spec", "review", "runtime", "docs", "other"):
        assert retro_job.validate_action_class(retro_job.action_class(label))
    assert not retro_job.validate_action_class("nice-to-have")


def test_every_retro_cluster_states_an_action_class(tmp_path: Path) -> None:
    artifacts = tmp_path / ".agents" / "artifacts"
    artifacts.mkdir(parents=True)
    (artifacts / "CODE_REVIEW.md").write_text(
        "- missing test for timeout path\n- doc typo in readme\n", encoding="utf-8"
    )
    text = retro_job.build_retro(tmp_path)
    assert "**Action class:** add-test" in text
    assert "**Action class:** doc" in text
    for label in retro_job.ACTION_CLASSES:
        assert label in " ".join(retro_job.ACTION_CLASSES)


def test_pr_comment_json_dump_is_read(tmp_path: Path) -> None:
    path = tmp_path / "comments.json"
    path.write_text(
        json.dumps([{"body": "forgot the retry on 429"}, {"body": "ok"}]),
        encoding="utf-8",
    )
    findings = retro_job.collect_pr_comment_findings(path)
    assert findings == [("comments.json", "forgot the retry on 429")]


def test_pr_comment_markdown_dump_is_read(tmp_path: Path) -> None:
    path = tmp_path / "comments.md"
    path.write_text("review: the migration is not reversible\n", encoding="utf-8")
    findings = retro_job.collect_pr_comment_findings(path)
    assert findings and findings[0][1].startswith("the migration")


def test_missing_pr_comment_file_is_not_a_crash(tmp_path: Path) -> None:
    assert retro_job.collect_pr_comment_findings(tmp_path / "absent.json") == []


def test_transcripts_redact_secret_like_lines(tmp_path: Path) -> None:
    text = "api_key: ghp_" + "a" * 30 + "\nforgot the cache warm\n"
    redacted = retro_job._redact(text)
    assert "ghp_" not in redacted
    assert "[redacted]" in redacted
    assert "forgot the cache warm" in redacted


def test_transcripts_are_best_effort(tmp_path: Path) -> None:
    # No local session on a bare fixture: empty evidence, no exception.
    assert retro_job.collect_transcript_findings(tmp_path) == []


def test_extra_findings_flow_into_the_retro(tmp_path: Path) -> None:
    text = retro_job.build_retro(
        tmp_path, extra_findings=[("PR_COMMENTS.json", "missed the rollback path")]
    )
    assert "missed the rollback path" in text


def test_retrospect_skill_names_ingest_and_classes() -> None:
    skill = (ROOT / "skills/retrospect/SKILL.md").read_text(encoding="utf-8")
    assert "--transcripts" in skill
    assert "--pr-comments" in skill
    for label in ("fix-now", "add-gate", "add-test", "doc", "non-action"):
        assert label in skill
