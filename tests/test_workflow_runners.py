"""Tests for the runner-label gate.

Covers AC-1 to AC-3 of the 2026-11-28 runner-label gate spec.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import check_workflow_runners as runners  # noqa: E402


def _repo(tmp_path: Path, workflows: dict[str, str] | None, allowlist: str | None) -> Path:
    if workflows is not None:
        wf = tmp_path / ".github" / "workflows"
        wf.mkdir(parents=True)
        for name, body in workflows.items():
            (wf / name).write_text(body, encoding="utf-8")
    if allowlist is not None:
        (tmp_path / ".github").mkdir(parents=True, exist_ok=True)
        (tmp_path / ".github" / "allowed-runners.txt").write_text(
            allowlist, encoding="utf-8"
        )
    return tmp_path


def _workflow(runs_on: str, job: str = "build") -> str:
    return (
        "name: ci\non: push\njobs:\n"
        f"  {job}:\n"
        "    runs-on: " + runs_on + "\n"
        "    steps:\n      - run: echo ok\n"
    )


def test_declared_label_passes(tmp_path: Path) -> None:
    root = _repo(tmp_path, {"ci.yml": _workflow("ubuntu-latest")}, "ubuntu-latest\n")
    report = runners.check(root)
    assert report.findings == []
    assert report.skip is None


def test_undeclared_label_fails_with_names(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path, {"ci.yml": _workflow("self-hosted")}, "ubuntu-latest\n")
    report = runners.check(root)
    assert len(report.findings) == 1
    finding = report.findings[0]
    assert finding.workflow.endswith("ci.yml")
    assert finding.job == "build"
    assert finding.label == "self-hosted"
    assert runners.main(["--root", str(root)]) == 1
    out = capsys.readouterr().out
    assert "ci.yml" in out and "build" in out and "self-hosted" in out


def test_no_workflows_skips(tmp_path: Path) -> None:
    root = _repo(tmp_path, None, "ubuntu-latest\n")
    report = runners.check(root)
    assert report.findings == []
    assert report.skip and "no .github/workflows" in report.skip


def test_no_allowlist_skips(tmp_path: Path) -> None:
    root = _repo(tmp_path, {"ci.yml": _workflow("self-hosted")}, None)
    report = runners.check(root)
    assert report.findings == []
    assert report.skip and "allowed-runners.txt" in report.skip


def test_empty_allowlist_fails(tmp_path: Path) -> None:
    root = _repo(tmp_path, {"ci.yml": _workflow("ubuntu-latest")}, "# none yet\n")
    report = runners.check(root)
    assert [f.label for f in report.findings] == ["ubuntu-latest"]


def test_list_valued_runs_on_checks_every_entry(tmp_path: Path) -> None:
    body = (
        "name: ci\non: push\njobs:\n  build:\n    runs-on: [ubuntu-latest, gpu-box]\n"
        "    steps:\n      - run: echo ok\n"
    )
    root = _repo(tmp_path, {"ci.yml": body}, "ubuntu-latest\n")
    report = runners.check(root)
    assert [f.label for f in report.findings] == ["gpu-box"]


def test_expression_is_unresolved_not_a_failure(tmp_path: Path) -> None:
    root = _repo(
        tmp_path, {"ci.yml": _workflow("${{ matrix.os }}")}, "ubuntu-latest\n"
    )
    report = runners.check(root)
    assert report.findings == []
    assert [item.split("/")[-1] for item in report.unresolved] == ["ci.yml:build"]


def test_unparsable_workflow_fails(tmp_path: Path) -> None:
    root = _repo(tmp_path, {"ci.yml": "jobs: [unclosed\n"}, "ubuntu-latest\n")
    report = runners.check(root)
    assert len(report.findings) == 1
    assert report.findings[0].reason == "cannot parse workflow"


def test_yaml_extension_is_scanned(tmp_path: Path) -> None:
    root = _repo(tmp_path, {"ci.yaml": _workflow("self-hosted")}, "ubuntu-latest\n")
    report = runners.check(root)
    assert [f.label for f in report.findings] == ["self-hosted"]
