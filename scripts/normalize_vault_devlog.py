#!/usr/bin/env python3
"""Normalize vault project dev-logs: newest-first + When/Kind backfill.

Usage::

  python3 scripts/normalize_vault_devlog.py --vault /opt/second-brain/vault
  python3 scripts/normalize_vault_devlog.py --vault … --project watchlist --dry-run

Does not invent history. Unparseable blocks keep relative order at the bottom
(after dated entries, still within the body).
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Import dual-zone helper from sibling module
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
try:
    from sync_vault_devlog import (  # type: ignore
        format_when_line,
        split_header_and_rest,
        _write_full,
    )
except Exception:  # pragma: no cover
    format_when_line = None  # type: ignore
    split_header_and_rest = None  # type: ignore
    _write_full = None  # type: ignore

H2_RE = re.compile(
    r"^##\s+(20\d{2}-\d{2}-\d{2})(?:T(\d{2}):(\d{2})(?::(\d{2}))?Z?)?\s*[—–-]\s*(.+?)\s*$"
)
BARE_RE = re.compile(
    r"^(20\d{2}-\d{2}-\d{2})\s*[—–-]\s*(.+?)\s*$"
)
WHEN_RE = re.compile(
    r"\*\*When:\*\*\s*(\d{4}-\d{2}-\d{2})\s+(\d{2}):(\d{2})\s*UTC",
    re.I,
)


class Entry:
    def __init__(
        self,
        heading: str,
        body_lines: list[str],
        sort_key: datetime,
        raw: str,
        orig_idx: int = 0,
    ) -> None:
        self.heading = heading
        self.body_lines = body_lines
        self.sort_key = sort_key
        self.raw = raw
        self.orig_idx = orig_idx

    def render(self) -> str:
        lines = [self.heading, ""]
        # strip leading blanks from body for rebuild
        body = self.body_lines[:]
        while body and not body[0].strip():
            body.pop(0)
        # ensure When / Kind at top of body
        has_when = any(ln.strip().startswith("- **When:**") for ln in body)
        has_kind = any(ln.strip().startswith("- **Kind:**") for ln in body)
        prefix: list[str] = []
        if not has_when and format_when_line is not None:
            prefix.append(format_when_line(self.sort_key))
        if not has_kind:
            kind = "release" if re.search(r"\bsynced\b", self.heading, re.I) else "note"
            prefix.append(f"- **Kind:** {kind}")
        if prefix:
            body = prefix + body
        # drop trailing empty
        while body and not body[-1].strip():
            body.pop()
        lines.extend(body)
        lines.append("")
        lines.append("")
        return "\n".join(lines)


def _parse_sort_key(heading: str, body: str) -> datetime:
    # Prefer When line
    m = WHEN_RE.search(body)
    if m:
        return datetime(
            int(m.group(1)[:4]),
            int(m.group(1)[5:7]),
            int(m.group(1)[8:10]),
            int(m.group(2)),
            int(m.group(3)),
            tzinfo=timezone.utc,
        )
    hm = H2_RE.match(heading.strip())
    if hm:
        y, mo, d = hm.group(1).split("-")
        hh = int(hm.group(2) or 12)
        mm = int(hm.group(3) or 0)
        ss = int(hm.group(4) or 0)
        return datetime(int(y), int(mo), int(d), hh, mm, ss, tzinfo=timezone.utc)
    # fallback epoch-ish stable
    return datetime(1970, 1, 1, tzinfo=timezone.utc)


def _coerce_bare_lines(text: str) -> str:
    """Turn bare 'YYYY-MM-DD — title' lines into ## headings when alone."""
    out: list[str] = []
    for line in text.splitlines():
        if BARE_RE.match(line) and not line.startswith("##"):
            out.append(f"## {line.strip()}")
        else:
            out.append(line)
    return "\n".join(out) + ("\n" if text.endswith("\n") else "")


def parse_entries(rest: str) -> tuple[list[Entry], list[str]]:
    """Parse ## blocks; return (dated_entries, unparseable_chunks as lines)."""
    if not rest.strip():
        return [], []
    rest = _coerce_bare_lines(rest)
    # split on ## starts
    chunks = re.split(r"(?=^## )", rest, flags=re.M)
    entries: list[Entry] = []
    unparsed: list[str] = []
    idx = 0
    for ch in chunks:
        if not ch.strip():
            continue
        if not ch.lstrip().startswith("## "):
            unparsed.append(ch if ch.endswith("\n") else ch + "\n")
            continue
        lines = ch.splitlines()
        heading = lines[0].strip()
        body = lines[1:]
        raw = ch if ch.endswith("\n") else ch + "\n"
        if not H2_RE.match(heading) and not re.match(r"^##\s+20\d{2}-\d{2}-\d{2}", heading):
            entries.append(
                Entry(
                    heading=heading,
                    body_lines=body,
                    sort_key=datetime(1970, 1, 1, tzinfo=timezone.utc),
                    raw=raw,
                    orig_idx=idx,
                )
            )
        else:
            key = _parse_sort_key(heading, "\n".join(body))
            entries.append(
                Entry(
                    heading=heading,
                    body_lines=body,
                    sort_key=key,
                    raw=raw,
                    orig_idx=idx,
                )
            )
        idx += 1
    return entries, unparsed


def standard_header(project_id: str) -> str:
    return (
        f"# {project_id} dev log\n\n"
        "Newest first. Times: UTC + HKT. Writers: harness `sync_vault_devlog` only.\n\n"
        f"Agent-appended development notes ({project_id} → optional knowledge vault).\n\n"
        "Two entry kinds (Option A — harness SoT):\n"
        "- **Release** (`/sync_docs`): `## YYYY-MM-DD — vX.Y.Z synced` + When/Kind/Release/…\n"
        "- **Note** (`--note`): `## YYYY-MM-DD — {title}` + When/Kind/Repo + bullets "
        "(never `synced` / bare semver title)\n\n"
    )


def normalize_text(text: str, project_id: str) -> str:
    if split_header_and_rest is None:
        raise RuntimeError("sync_vault_devlog helpers unavailable")
    # Force standard header; keep nothing from old header except we replace entirely
    coerced = _coerce_bare_lines(text)
    _old_header, rest = split_header_and_rest(coerced)
    entries, unparsed = parse_entries(rest)
    # newest first; same-day: higher orig_idx (later append) first
    entries.sort(key=lambda e: (e.sort_key, e.orig_idx), reverse=True)
    body = "".join(e.render() for e in entries)
    if unparsed:
        body += "\n<!-- unparsed legacy blocks -->\n" + "".join(unparsed)
    return standard_header(project_id) + body


def normalize_file(path: Path, *, dry_run: bool = False) -> str:
    project_id = path.parent.name
    text = path.read_text(encoding="utf-8")
    new = normalize_text(text, project_id)
    if dry_run:
        return new
    if _write_full is not None:
        _write_full(path, new)
    else:
        path.write_text(new, encoding="utf-8")
    return new


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--vault",
        type=Path,
        default=Path("/opt/second-brain/vault"),
        help="Vault root",
    )
    ap.add_argument(
        "--project",
        action="append",
        dest="projects",
        help="Only these project ids (repeatable). Default: all with dev-log.md",
    )
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    vault = args.vault.expanduser().resolve()
    root = vault / "01-Projects"
    if not root.is_dir():
        print(f"❌ no 01-Projects under {vault}", file=sys.stderr)
        return 1
    paths = sorted(root.glob("*/dev-log.md"))
    if args.projects:
        want = set(args.projects)
        paths = [p for p in paths if p.parent.name in want]
    if not paths:
        print("No dev-log.md found")
        return 0
    for path in paths:
        try:
            old = path.read_text(encoding="utf-8")
            new = normalize_text(old, path.parent.name)
            changed = old != new
            status = "dry-run" if args.dry_run else ("updated" if changed else "unchanged")
            if not args.dry_run and changed:
                normalize_file(path, dry_run=False)
            print(f"{'✅' if changed or args.dry_run else '·'} {path.parent.name}: {status} ({len(new)} bytes)")
            if args.dry_run and changed:
                # show first entry heading
                m = re.search(r"^## .+$", new, re.M)
                if m:
                    print(f"    top → {m.group(0)[:80]}")
        except Exception as exc:  # noqa: BLE001
            print(f"❌ {path.parent.name}: {exc}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
