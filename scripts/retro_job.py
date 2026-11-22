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


def build_retro(root: Path, when: datetime | None = None) -> str:
    when = when or datetime.now(UTC)
    findings = collect_findings(root)
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


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    root = args.root.resolve()
    text = build_retro(root)
    if args.dry_run:
        print(text)
        return 0
    path = write_retro(root, text, args.out)
    print(f"✅ retro written: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
