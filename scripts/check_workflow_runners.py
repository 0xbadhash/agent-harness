#!/usr/bin/env python3
"""Fail when a workflow names a runner label this repo has not declared.

The allowlist is a declaration, not a registry read: GitHub does not expose
runner registration without an admin-scoped token. Declaring intent in the repo
is deterministic and catches the common failure, a label copied from another
repository. ``runs-on`` expressions are reported as unresolved and do not fail.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

WORKFLOWS = Path(".github") / "workflows"
ALLOWLIST = Path(".github") / "allowed-runners.txt"


@dataclass(frozen=True)
class Finding:
    """One workflow job that names a label the allowlist does not declare."""

    workflow: str
    job: str
    label: str
    reason: str = "not declared"


@dataclass
class Report:
    """Gate result for one repository."""

    findings: list[Finding] = field(default_factory=list)
    unresolved: list[str] = field(default_factory=list)
    skip: str | None = None
    workflows: int = 0
    declared: int = 0

    @property
    def ok(self) -> bool:
        return not self.findings


def read_allowlist(path: Path) -> set[str]:
    """One label per line; ``#`` starts a comment."""
    labels: set[str] = set()
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        label = line.split("#", 1)[0].strip()
        if label:
            labels.add(label)
    return labels


def _load(path: Path) -> tuple[dict, str | None]:
    """Return the parsed workflow and a reason when it cannot be read."""
    try:
        import yaml
    except ImportError:
        return {}, "PyYAML is not installed"
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8", errors="replace"))
    except yaml.YAMLError:
        return {}, "cannot parse workflow"
    return (data if isinstance(data, dict) else {}), None


def _labels(runs_on: object) -> list[str]:
    if isinstance(runs_on, str):
        return [runs_on.strip()]
    if isinstance(runs_on, list):
        return [str(item).strip() for item in runs_on if str(item).strip()]
    return []


def check(root: Path) -> Report:
    """Scan ``root`` for workflow jobs whose runner label is undeclared."""
    root = Path(root).resolve()
    workflows_dir = root / WORKFLOWS
    if not workflows_dir.is_dir():
        return Report(skip="no .github/workflows — nothing to check")
    paths = sorted(workflows_dir.glob("*.yml")) + sorted(workflows_dir.glob("*.yaml"))
    if not paths:
        return Report(skip="no workflow files in .github/workflows")

    allow_path = root / ALLOWLIST
    if not allow_path.is_file():
        return Report(
            skip="no .github/allowed-runners.txt — declare labels to enable the gate"
        )
    declared = read_allowlist(allow_path)

    report = Report(workflows=len(paths), declared=len(declared))
    for path in paths:
        rel = path.relative_to(root).as_posix()
        data, error = _load(path)
        if error:
            report.findings.append(Finding(rel, "-", "-", error))
            continue
        jobs = data.get("jobs")
        if not isinstance(jobs, dict):
            continue
        for job_id, job in jobs.items():
            if not isinstance(job, dict):
                continue
            for label in _labels(job.get("runs-on")):
                if label.startswith("${{"):
                    report.unresolved.append(f"{rel}:{job_id}")
                elif label not in declared:
                    report.findings.append(Finding(rel, str(job_id), label))

    report.findings.sort(key=lambda f: (f.workflow, f.job, f.label))
    return report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=".", help="repository root")
    ap.add_argument("--json", action="store_true", help="emit the report as JSON")
    args = ap.parse_args(argv)

    report = check(Path(args.root))
    if args.json:
        print(
            json.dumps(
                {
                    "ok": report.ok,
                    "skip": report.skip,
                    "workflows": report.workflows,
                    "declared": report.declared,
                    "unresolved": report.unresolved,
                    "findings": [f.__dict__ for f in report.findings],
                },
                indent=2,
            )
        )
        return 0 if report.ok else 1

    if report.skip:
        print(f"skip: {report.skip}")
        return 0
    for finding in report.findings:
        print(
            f"fail: {finding.workflow}:{finding.job} uses runner "
            f"{finding.label} ({finding.reason})"
        )
    if report.findings:
        return 1
    note = f", {len(report.unresolved)} unresolved expression(s)" if report.unresolved else ""
    print(
        f"ok: {report.workflows} workflow(s), {report.declared} runner label(s) "
        f"declared{note}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
