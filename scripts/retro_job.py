#!/usr/bin/env python3
"""Post-ship retro: turn review comments, waivers, and transcripts into checks.

Deterministic and offline. Sources are files already on disk:

- ``.agents/artifacts/CODE_REVIEW.md`` / ``CROSS_REVIEW.md`` / ``PLAN_REVIEW.md``
  (findings and fix lines)
- ``.agents/artifacts/*TRANSCRIPT*.md`` (sanitized session excerpts, optional)
- ``.agents/artifacts/WAIVER_LOG.jsonl`` (waiver reasons)

Output is one markdown retro under ``docs/retros/`` with clustered lessons and
a proposed ratchet check per cluster. It never edits gates automatically; a
human promotes a proposal into a gate or a lint-ratchet baseline.

Usage::

  python3 scripts/retro_job.py --root .
  python3 scripts/retro_job.py --root . --since 2026-11-01 --dry-run
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARTIFACTS = Path(".agents") / "artifacts"
FINDING_RE = re.compile(
    r"^\s*(?:[-*]|\d+\.)\s+(?:P[0-3]\s*[:—-]?\s*)?(.+)$", re.IGNORECASE
)
FIX_RE = re.compile(r"^\s*Fix:\s*(.+)$", re.IGNORECASE)

# Cluster labels are deliberately small and stable; the retro proposes one
# ratchet sink per label instead of a generic "be more careful".
CLUSTERS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("tests", re.compile(r"\b(test|pytest|coverage|regression|fixture)\b", re.I)),
    ("spec", re.compile(r"\b(spec|acceptance|ac-\d+|grill|glossary)\b", re.I)),
    ("review", re.compile(r"\b(review|finding|reviewer|axis|verdict)\b", re.I)),
    ("docs", re.compile(r"\b(doc|readme|changelog|comment|typo)\b", re.I)),
    ("runtime", re.compile(r"\b(runtime|timeout|port|smoke|deploy|env)\b", re.I)),
)


ACTION_CLASSES = ("fix-now", "add-gate", "add-test", "doc", "non-action")
ACTION_BY_LABEL = {
    "tests": "add-test",
    "spec": "add-gate",
    "review": "add-gate",
    "runtime": "fix-now",
    "docs": "doc",
    "other": "non-action",
}
PR_COMMENT_RE = re.compile(r"^\s*(?:[-*]|review:)\s+(.+)$", re.IGNORECASE)


def action_class(label: str) -> str:
    """Return the action class for a cluster label."""
    return ACTION_BY_LABEL.get(label, "non-action")


def validate_action_class(value: str) -> bool:
    """Return True when value is one of the five action classes."""
    return value in ACTION_CLASSES


def _redact(text: str) -> str:
    """Drop secret-like lines before evidence is written."""
    out: list[str] = []
    for line in text.splitlines():
        if re.search(r"(BEGIN [A-Z ]*PRIVATE KEY|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{20,}|xox[baprs]-)", line):
            out.append("[redacted]")
        else:
            out.append(line)
    return "\n".join(out)


def collect_transcript_findings(root: Path, since_days: int = 14) -> list[tuple[str, str]]:
    """Render the most recent local session with the existing helper."""
    helper = Path(__file__).resolve().parent / "agent_transcript.py"
    if not helper.is_file():
        return []
    find = subprocess.run(
        [sys.executable, str(helper), "find", "--cwd", str(root), "--since-days", str(since_days)],
        capture_output=True,
        text=True,
        check=False,
    )
    sessions = [line.strip() for line in find.stdout.splitlines() if line.strip()]
    if find.returncode != 0 or not sessions:
        return []
    session = sessions[-1]
    out = root / ARTIFACTS / "SESSION_TRANSCRIPT.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    render = subprocess.run(
        [sys.executable, str(helper), "render", "--session", session, "--out", str(out)],
        capture_output=True,
        text=True,
        check=False,
    )
    if render.returncode != 0 or not out.is_file():
        return []
    out.write_text(_redact(out.read_text(encoding="utf-8", errors="replace")), encoding="utf-8")
    findings: list[tuple[str, str]] = []
    for line in out.read_text(encoding="utf-8", errors="replace").splitlines():
        if re.search(r"\b(should have|forgot|missed|root cause|retry|failed)\b", line, re.I):
            findings.append((out.name, line.strip(" -")[:300]))
    return findings


def collect_pr_comment_findings(path: Path) -> list[tuple[str, str]]:
    """Read a saved PR review-comment dump (JSON or markdown)."""
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8", errors="replace")
    findings: list[tuple[str, str]] = []
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        data = None
    if isinstance(data, list):
        for row in data:
            body = str((row or {}).get("body") or "").strip()
            if len(body) >= 12:
                findings.append((path.name, body))
        return findings
    for line in text.splitlines():
        match = PR_COMMENT_RE.match(line)
        if match and len(match.group(1).strip()) >= 12:
            findings.append((path.name, match.group(1).strip()))
    return findings


def collect_findings(root: Path) -> list[tuple[str, str]]:
    """Return (source, line) for review findings already on disk."""
    out: list[tuple[str, str]] = []
    for name in ("CODE_REVIEW.md", "CROSS_REVIEW.md", "PLAN_REVIEW.md"):
        path = root / ARTIFACTS / name
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            fix = FIX_RE.match(line)
            if fix:
                out.append((name, fix.group(1).strip()))
                continue
            match = FINDING_RE.match(line)
            if match and len(match.group(1).strip()) >= 12:
                out.append((name, match.group(1).strip()))
    for path in sorted((root / ARTIFACTS).glob("*TRANSCRIPT*.md")):
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if re.search(r"\b(should have|forgot|missed|root cause)\b", line, re.I):
                out.append((path.name, line.strip(" -")))
    return out


def collect_waivers(root: Path) -> list[dict]:
    log = root / ARTIFACTS / "WAIVER_LOG.jsonl"
    if not log.is_file():
        return []
    rows: list[dict] = []
    for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


def cluster_lessons(findings: list[tuple[str, str]]) -> dict[str, list[str]]:
    clusters: dict[str, list[str]] = {}
    for _, text in findings:
        labels = [label for label, pattern in CLUSTERS if pattern.search(text)]
        for label in labels or ["other"]:
            clusters.setdefault(label, []).append(text)
    return clusters


def _proposal(label: str, examples: list[str]) -> str:
    sample = examples[0][:100]
    if label == "tests":
        return (
            "Ratchet: add a regression test before the fix and reference it from "
            f"the PR body. Example: {sample}"
        )
    if label == "spec":
        return (
            "Ratchet: make the missing AC/grill/glossary item a spec-gate failure. "
            f"Example: {sample}"
        )
    if label == "review":
        return (
            "Ratchet: add the review finding to the two-axis checklist so the next "
            f"review catches it. Example: {sample}"
        )
    if label == "runtime":
        return (
            "Ratchet: add the runtime condition to the night-shift or smoke gate. "
            f"Example: {sample}"
        )
    if label == "docs":
        return f"Ratchet: add a docs/comment lint rule for this pattern. Example: {sample}"
    return f"Ratchet: inspect this finding and choose a gate sink. Example: {sample}"


def build_retro(
    root: Path,
    when: datetime | None = None,
    *,
    extra_findings: list[tuple[str, str]] | None = None,
) -> str:
    when = when or datetime.now(UTC)
    findings = collect_findings(root) + list(extra_findings or [])
    waivers = collect_waivers(root)
    clusters = cluster_lessons(findings)
    waiver_types = Counter(str(row.get("waiver_type") or "?") for row in waivers)
    lines = [
        f"# Retro — {when.strftime('%Y-%m-%d')}",
        "",
        "**Source:** local artifacts only (reviews, transcripts, waiver ledger).",
        f"**Findings:** {len(findings)} · **Waivers:** {len(waivers)}",
        "",
        "## Clusters",
        "",
    ]
    if not clusters:
        lines.append("_No review findings on disk — nothing to cluster._")
    for label in sorted(clusters, key=lambda key: (-len(clusters[key]), key)):
        examples = clusters[label]
        lines.extend(
            [
                f"### {label} ({len(examples)})",
                "",
                f"**Action class:** {action_class(label)}",
                "",
                f"**Proposal:** {_proposal(label, examples)}",
                "",
                "Examples:",
                *[f"- {item[:220]}" for item in examples[:5]],
                "",
            ]
        )
    lines.extend(["## Waivers", ""])
    if waiver_types:
        lines.append("| Type | Count |")
        lines.append("|------|-------|")
        for kind, count in sorted(waiver_types.items()):
            lines.append(f"| {kind} | {count} |")
    else:
        lines.append("_No waivers recorded._")
    lines.extend(
        [
            "",
            "## Promotion checklist",
            "",
            "- [ ] Every cluster carries one of: fix-now, add-gate, add-test, doc, non-action",
            "- [ ] Each cluster has one gate or ratchet-baseline change proposed",
            "- [ ] No finding is closed by prose alone",
            "- [ ] Baseline updated with `python3 scripts/check_lint_ratchet.py --update` when a rule improves",
            "",
        ]
    )
    return "\n".join(lines)


def write_retro(root: Path, text: str, out: Path | None = None) -> Path:
    target = out or (root / "docs" / "retros" / f"{datetime.now(UTC):%Y-%m-%d}-retro.md")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    return target


def _slug(label: str) -> str:
    return re.sub(r"[^a-z0-9_-]+", "-", label.lower()).strip("-") or "other"


def _cluster_body(label: str, examples: list[str], when: datetime) -> str:
    lines = [
        f"# [retro] {label}: {len(examples)} finding(s)",
        "",
        f"**Source:** retro {when:%Y-%m-%d}",
        f"**Action class:** {action_class(label)}",
        f"**Proposal:** {_proposal(label, examples)}",
        "",
        "## Examples",
        "",
        *[f"- {item}" for item in examples[:20]],
        "",
        "## Promotion checklist",
        "",
        "- [ ] Add one automated gate or ratchet-baseline change for this cluster",
        "- [ ] Reference the change from the next PR body",
        "",
    ]
    return "\n".join(lines)


def _umbrella_body(clusters: dict[str, list[str]], when: datetime) -> str:
    lines = [
        f"# [retro] Umbrella — {when:%Y-%m-%d}",
        "",
        "Umbrella for the retro clusters below. Each cluster has its own issue body.",
        "",
        "| Cluster | Findings |",
        "|---------|----------|",
        *[f"| {label} | {len(items)} |" for label, items in sorted(clusters.items())],
        "",
        "- [ ] Each cluster is promoted to one gate or ratchet change",
        "- [ ] No cluster is closed by prose alone",
        "",
    ]
    return "\n".join(lines)


def write_issue_bodies(
    root: Path,
    clusters: dict[str, list[str]],
    when: datetime | None = None,
    out_dir: Path | None = None,
) -> list[Path]:
    """Write one issue body per cluster plus an umbrella body."""
    when = when or datetime.now(UTC)
    target = out_dir or (root / ".agents" / "artifacts" / "issues")
    target.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for label, examples in sorted(clusters.items()):
        path = target / f"{when:%Y-%m-%d}-{_slug(label)}.md"
        path.write_text(_cluster_body(label, examples, when), encoding="utf-8")
        written.append(path)
    umbrella = target / f"{when:%Y-%m-%d}-umbrella.md"
    umbrella.write_text(_umbrella_body(clusters, when), encoding="utf-8")
    written.append(umbrella)
    return written


def _title_from_body(path: Path) -> str:
    first = path.read_text(encoding="utf-8", errors="replace").splitlines()[0]
    return first.lstrip("# ").strip()


def _gh_create(body: Path, repo: str | None) -> int:
    argv = ["gh", "issue", "create", "--title", _title_from_body(body), "--body-file", str(body)]
    if repo:
        argv.extend(["--repo", repo])
    run = subprocess.run(argv, capture_output=True, text=True, check=False)
    if run.returncode != 0:
        print(run.stderr.strip() or "gh issue create failed", file=sys.stderr)
        return run.returncode
    print(run.stdout.strip())
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument(
        "--file-issues",
        action="store_true",
        help="Write one Markdown issue body per cluster plus an umbrella body",
    )
    ap.add_argument(
        "--gh",
        action="store_true",
        help="Create the written issue bodies with gh (requires --file-issues)",
    )
    ap.add_argument("--repo", default=None, help="owner/name passed to gh issue create")
    ap.add_argument("--issues-dir", type=Path, default=None)
    ap.add_argument(
        "--transcripts",
        action="store_true",
        help="Render the most recent local session as retro evidence (redacted)",
    )
    ap.add_argument(
        "--pr-comments",
        type=Path,
        default=None,
        help="Saved PR review-comment dump (JSON list or markdown)",
    )
    ap.add_argument(
        "--fetch-pr-comments",
        action="store_true",
        help="Fetch review threads with gh (requires --pr and --gh approval)",
    )
    ap.add_argument("--pr", type=int, default=None, help="PR number for --fetch-pr-comments")
    args = ap.parse_args(argv)
    if args.gh and not args.file_issues:
        print("❌ --gh requires --file-issues", file=sys.stderr)
        return 2
    if args.fetch_pr_comments and args.pr is None:
        print("❌ --fetch-pr-comments requires --pr", file=sys.stderr)
        return 2
    root = args.root.resolve()

    extra: list[tuple[str, str]] = []
    if args.transcripts:
        extra.extend(collect_transcript_findings(root))
        if not extra:
            print("note: no local session transcript found — transcripts skipped", file=sys.stderr)
    if args.pr_comments is not None:
        extra.extend(collect_pr_comment_findings(args.pr_comments))
    if args.fetch_pr_comments:
        fetched = root / ARTIFACTS / "PR_COMMENTS.json"
        fetched.parent.mkdir(parents=True, exist_ok=True)
        run = subprocess.run(
            ["gh", "pr", "view", str(args.pr), "--json", "reviews,comments"],
            capture_output=True,
            text=True,
            check=False,
        )
        if run.returncode != 0:
            print(run.stderr.strip() or "gh pr view failed", file=sys.stderr)
            return run.returncode
        fetched.write_text(_redact(run.stdout), encoding="utf-8")
        extra.extend(collect_pr_comment_findings(fetched))

    text = build_retro(root, extra_findings=extra)
    if args.dry_run:
        print(text)
        return 0
    path = write_retro(root, text, args.out)
    print(f"✅ retro written: {path}")
    if not args.file_issues:
        return 0
    clusters = cluster_lessons(collect_findings(root))
    bodies = write_issue_bodies(root, clusters, out_dir=args.issues_dir)
    for body in bodies:
        print(f"✅ issue body: {body}")
    if args.gh:
        for body in bodies:
            rc = _gh_create(body, args.repo)
            if rc != 0:
                return rc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
