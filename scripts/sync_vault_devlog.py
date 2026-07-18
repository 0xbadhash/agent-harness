#!/usr/bin/env python3
"""Vault dev-log writers (two kinds — Option A).

1. **Release** (after ``/sync_docs``): structured ``## date — vX.Y.Z synced`` block
   with Release / Scope / Tests / Next (Shaping) / Pipeline / Repo / Task.
   Default CLI with no ``--note``.

2. **Ad-hoc note** (mid-task): ``## YYYY-MM-DD — {title}`` + bullets — **never**
   contains the word ``synced`` or a bare semver title. Use::

     python3 scripts/sync_vault_devlog.py --note "short title" \\
       --bullet "Changed: path" --bullet "Outcome: ..."

Do not raw ``cat >>`` into the vault; that mixed freeform with release rows.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# Vault optional — never hardcode a host path (public harness is vault-agnostic).
DEFAULT_VAULT = None


def _project_label() -> str:
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from vault_resolve import load_vault_config

        return load_vault_config(ROOT).get("project_label") or "product"
    except Exception:
        plugin = ROOT / ".agents" / "product_plugin.yaml"
        if plugin.is_file():
            m = re.search(r"^\s*project_label:\s*(.+)$", plugin.read_text(), re.M)
            if m:
                return m.group(1).strip().strip("\"'")
            m = re.search(r"^\s*product_id:\s*(.+)$", plugin.read_text(), re.M)
            if m:
                return m.group(1).strip().strip("\"'")
        return "product"


def _dev_log_rel() -> Path:
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from vault_resolve import load_vault_config

        rel = (load_vault_config(ROOT).get("dev_log_rel") or "").strip()
        if rel:
            return Path(rel)
    except Exception:
        pass
    return Path(f"01-Projects/{_project_label()}/dev-log.md")


DEV_LOG_REL = _dev_log_rel()
_LABEL = _project_label()
DEV_LOG_HEADER = (
    f"# {_LABEL} dev log\n\n"
    "Newest first. Times: UTC + HKT. Writers: harness `sync_vault_devlog` only.\n\n"
    f"Agent-appended development notes ({_LABEL} → optional knowledge vault).\n\n"
    "Two entry kinds (Option A — harness docs/dev-log.md):\n"
    "- **Release** (`/sync_docs`): `## YYYY-MM-DD — vX.Y.Z synced` + When/Kind/Release/…\n"
    "- **Note** (`--note`): `## YYYY-MM-DD — {title}` + When/Kind/Repo + bullets "
    "(never `synced` / bare semver title)\n\n"
)  # keep in sync with ensure_dev_log.standard_header
SHAPING_MAX = 3
ROADMAP_PATH = ROOT / "BACKEND_ROADMAP.md"
WORKFLOW_PATH = ROOT / "WORKFLOW_DOCUMENTATION.md"
RUNBOOK_PATH = ROOT / "RELEASE_RUNBOOK.md"
HKT_ZONE = "Asia/Hong_Kong"


def _git_tag() -> str:
    r = subprocess.run(
        ["git", "describe", "--tags", "--abbrev=0"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if r.returncode == 0 and r.stdout.strip():
        return r.stdout.strip()
    return "unknown"


def _first_int(text: str) -> int | None:
    m = re.search(r"\d+", text)
    return int(m.group(0)) if m else None


def _smoke_cell(line: str) -> str:
    """Middle cell of a markdown table row `| Check | Result |`."""
    parts = [p.strip() for p in line.strip().strip("|").split("|")]
    if len(parts) >= 2:
        return parts[-1]
    return ""


def _parse_release_runbook(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    version = "unknown"
    m = re.search(r"\*\*Version:\*\*\s*`([^`]+)`", text)
    if m:
        version = m.group(1).strip()
    else:
        m = re.search(
            r"^#\s+Release Runbook\s*[—–-]\s*(v?\d+\.\d+\.\d+\S*)",
            text,
            re.MULTILINE | re.IGNORECASE,
        )
        if m:
            version = m.group(1).strip()
            if not version.startswith("v") and re.match(r"\d", version):
                version = f"v{version}"

    theme = ""
    tm = re.search(r"\*\*Theme:\*\*\s*(.+)", text)
    if tm:
        theme = tm.group(1).strip()

    scope = ""
    sm = re.search(r"## Release scope\s+Since[^\n]*\.\s*([^\n|]+)", text)
    if sm:
        scope = sm.group(1).strip()
    if not scope and theme:
        scope = theme
    # Summary first bullet as weak scope fallback
    if not scope:
        sum_m = re.search(r"## Summary\s*\n+((?:[-*].+\n?)+)", text)
        if sum_m:
            first = sum_m.group(1).strip().splitlines()[0]
            scope = re.sub(r"^[-*]\s+", "", first).strip()

    phpunit = pytest = validate = ""
    for line in text.splitlines():
        low = line.lower()
        if not line.strip().startswith("|"):
            continue
        if "phpunit" in low and "check" not in low.split("|")[0].lower():
            # row like | PHPUnit | 286 / 0 failures |
            if "phpunit" in (line.split("|")[1].strip().lower() if "|" in line else ""):
                phpunit = _smoke_cell(line)
        if re.search(r"\|\s*pytest\s*\|", line, re.I):
            pytest = _smoke_cell(line)
        if re.search(r"\|\s*validate", line, re.I) or (
            "compliance" in low and "validate" in low
        ):
            validate = _smoke_cell(line)

    return {
        "version": version,
        "scope": scope,
        "theme": theme,
        "phpunit": phpunit,
        "pytest": pytest,
        "validate": validate,
    }


def format_tests_line(runbook: dict[str, str]) -> str:
    """Human Tests: line with optional total of PHPUnit + pytest counts."""
    bits: list[str] = []
    n_php = n_py = None
    if runbook.get("phpunit"):
        bits.append(f"PHPUnit {runbook['phpunit']}")
        n_php = _first_int(runbook["phpunit"])
    if runbook.get("pytest"):
        bits.append(f"pytest {runbook['pytest']}")
        n_py = _first_int(runbook["pytest"])
    if runbook.get("validate"):
        bits.append(f"validate {runbook['validate']}")
    if not bits:
        return "see RELEASE_RUNBOOK.md smoke table"
    line = ", ".join(bits)
    if n_php is not None and n_py is not None:
        line += f" · **total: {n_php + n_py}**"
    elif n_php is not None:
        line += f" · **total: {n_php}** (PHPUnit only)"
    return line


def _section_body(text: str, *headers: str) -> str:
    """Return body under the first matching #..### header until next same-or-higher heading."""
    for header in headers:
        # e.g. ## Shaping / ## Next (Shaping) / ## Open backlog (ordered)
        pat = re.compile(
            rf"^(#{{1,3}})\s+.*{re.escape(header)}.*\s*$",
            re.MULTILINE | re.IGNORECASE,
        )
        m = pat.search(text)
        if not m:
            continue
        level = len(m.group(1))
        start = m.end()
        rest = text[start:]
        end_m = re.search(rf"^#{{1,{level}}}\s+\S", rest, re.MULTILINE)
        return rest[: end_m.start()] if end_m else rest
    return ""


def _open_bullets(body: str, limit: int = SHAPING_MAX) -> list[str]:
    items: list[str] = []
    for line in body.splitlines():
        s = line.strip()
        if not s:
            continue
        # skip done checkboxes / checkmarks
        if re.search(r"\[x\]|\[X\]|✅", s):
            continue
        if s.startswith("|") and re.search(r"shipped|done|✅", s, re.I):
            continue
        m = re.match(r"^[-*]\s+(?:\[\s\]\s+)?(.+)$", s)
        if m:
            item = m.group(1).strip()
            item = re.sub(r"\s+", " ", item)
            if item and not item.startswith("<!--"):
                items.append(item)
                if len(items) >= limit:
                    break
    return items


def _parse_shaping_section(*paths: Path) -> list[str]:
    """Option 3 primary: ## Shaping or ## Next (Shaping) open bullets."""
    for path in paths:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for title in ("Next (Shaping)", "Shaping"):
            body = _section_body(text, title)
            if not body.strip():
                continue
            items = _open_bullets(body)
            if items:
                return items
    return []


def _parse_roadmap_open(path: Path, limit: int = SHAPING_MAX) -> list[str]:
    """Fallback: first open #### items under ## Open backlog (no ✅ in heading)."""
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8")
    body = _section_body(text, "Open backlog")
    if not body.strip():
        # whole file scan for #### N. Title without ✅
        body = text

    items: list[str] = []
    for m in re.finditer(r"^####\s+(.+)$", body, re.MULTILINE):
        title = m.group(1).strip()
        if "✅" in title or re.search(r"\[✅\]|\[x\]", title, re.I):
            continue
        # skip if next few lines only say Done with checkmark-only archive
        items.append(re.sub(r"\s+", " ", title))
        if len(items) >= limit:
            break

    # table rows in Deferred / Open with Priority column OPEN-ish
    if not items:
        for line in body.splitlines():
            if not line.strip().startswith("|"):
                continue
            if re.search(r"\|\s*#\s*\|", line) or "---" in line:
                continue
            if re.search(r"shipped|✅|\*\*✅\*\*", line, re.I):
                continue
            if re.search(r"\bopen\b|\bpartial\b|\bbacklog\b|\bdeferred\b", line, re.I):
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                label = " — ".join(c for c in cells[:3] if c)
                if label:
                    items.append(label)
                    if len(items) >= limit:
                        break
    return items


def parse_shaping_next(
    *,
    roadmap: Path = ROADMAP_PATH,
    workflow: Path = WORKFLOW_PATH,
    runbook: Path = RUNBOOK_PATH,
    limit: int = SHAPING_MAX,
) -> list[str]:
    """Option 3: Shaping section first, then open roadmap items."""
    items = _parse_shaping_section(roadmap, workflow, runbook)
    if items:
        return items[:limit]
    return _parse_roadmap_open(roadmap, limit=limit)


def format_shaping_line(items: list[str]) -> str:
    if not items:
        return "_(none)_"
    return "; ".join(items)


def _parse_workflow_last_release(path: Path) -> str:
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    m = re.search(r"\*\*Last Release:\*\*\s*`([^`]+)`\s*—\s*(.+)", text)
    if m:
        return f"{m.group(1)} — {m.group(2).strip()}"
    return ""


def _pipeline_task(path: Path) -> str:
    if not path.is_file():
        return ""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return ""
    return str(data.get("task") or "")


def _as_utc(when: datetime | None) -> datetime:
    dt = when or datetime.now(timezone.utc)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def format_when_line(when: datetime | None = None) -> str:
    """Dual-zone timestamp line for every dev-log entry."""
    utc = _as_utc(when)
    try:
        from zoneinfo import ZoneInfo

        hkt = utc.astimezone(ZoneInfo(HKT_ZONE))
    except Exception:  # noqa: BLE001 — portable fallback UTC+8
        from datetime import timedelta

        hkt = utc + timedelta(hours=8)
    return (
        f"- **When:** {utc.strftime('%Y-%m-%d %H:%M')} UTC · "
        f"{hkt.strftime('%Y-%m-%d %H:%M')} HKT"
    )


def split_header_and_rest(text: str) -> tuple[str, str]:
    """Split file into preamble (before first ## entry) and rest."""
    if not text:
        return DEV_LOG_HEADER, ""
    lines = text.splitlines(keepends=True)
    cut = None
    for i, line in enumerate(lines):
        if line.startswith("## "):
            cut = i
            break
    if cut is None:
        header = text if text.endswith("\n") else text + "\n"
        if not header.endswith("\n\n"):
            header = header.rstrip("\n") + "\n\n"
        return header, ""
    header = "".join(lines[:cut])
    rest = "".join(lines[cut:])
    if header and not header.endswith("\n"):
        header += "\n"
    if header and not header.endswith("\n\n"):
        header = header.rstrip("\n") + "\n\n"
    return header, rest


def _write_full(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.write_text(content, encoding="utf-8")
    except PermissionError:
        proc = subprocess.run(
            ["sudo", "-u", "secondbrain", "tee", str(path)],
            input=content.encode("utf-8"),
            capture_output=True,
            check=False,
        )
        if proc.returncode != 0:
            raise PermissionError(
                f"cannot write {path}: {proc.stderr.decode(errors='replace')}".strip()
            )


def prepend_entry(dev_log: Path, content: str, *, init_header: bool = True) -> None:
    """Insert entry after file header (newest-first). Content should end with newline."""
    body = content if content.endswith("\n") else content + "\n"
    if init_header and (not dev_log.is_file() or dev_log.stat().st_size == 0):
        _write_full(dev_log, DEV_LOG_HEADER + body)
        return
    existing = ""
    if dev_log.is_file():
        try:
            existing = dev_log.read_text(encoding="utf-8")
        except OSError:
            existing = ""
    header, rest = split_header_and_rest(existing if existing else DEV_LOG_HEADER)
    if not header.strip():
        header = DEV_LOG_HEADER
    _write_full(dev_log, header + body + ("\n" if body and rest and not body.endswith("\n\n") else "") + rest)


def build_entry(
    *,
    tag: str,
    runbook: dict[str, str],
    workflow_release: str,
    pipeline_task: str,
    shaping: list[str] | None = None,
    synced_at: datetime | None = None,
) -> str:
    now = _as_utc(synced_at)
    day = now.strftime("%Y-%m-%d")
    version = runbook.get("version") or tag
    if version == "unknown" and tag != "unknown":
        version = tag
    scope = runbook.get("scope") or workflow_release or "(see RELEASE_RUNBOOK.md)"
    tests_line = format_tests_line(runbook)
    shaping_line = format_shaping_line(shaping if shaping is not None else [])

    lines = [
        f"## {day} — {version} synced",
        "",
        format_when_line(now),
        "- **Kind:** release",
        f"- **Release:** `{version}` (tag `{tag}`)",
        f"- **Scope:** {scope}",
    ]
    if runbook.get("theme") and runbook["theme"] != scope:
        lines.append(f"- **Theme:** {runbook['theme']}")
    lines.extend(
        [
            f"- **Tests:** {tests_line}",
            f"- **Next (Shaping):** {shaping_line}",
            "- **Pipeline:** shipped → init",
            f"- **Repo:** `{ROOT}`",
        ]
    )
    if pipeline_task:
        lines.append(f"- **Task:** {pipeline_task}")
    lines.append("")
    return "\n".join(lines)


def _entry_marker(tag: str, version: str) -> str:
    needle = version if version and version != "unknown" else tag
    # normalize so `v2.3.12 synced` matches
    if needle.startswith("v") is False and re.match(r"\d+\.\d+", needle):
        needle = f"v{needle}"
    return f"{needle} synced"


def entry_exists(dev_log: Path, marker: str) -> bool:
    if not dev_log.is_file():
        return False
    text = dev_log.read_text(encoding="utf-8")
    if marker in text:
        return True
    # also treat bare version without v
    alt = marker[1:] if marker.startswith("v") else f"v{marker}"
    return alt in text


def _append_as_secondbrain(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        ["sudo", "-u", "secondbrain", "tee", "-a", str(path)],
        input=content.encode("utf-8"),
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise PermissionError(
            f"cannot write {path}: {proc.stderr.decode(errors='replace')}".strip()
        )


def append_entry(dev_log: Path, content: str, *, init_header: bool = True) -> None:
    """Compat alias — all writers prepend (newest-first)."""
    prepend_entry(dev_log, content, init_header=init_header)


def night_shift_day_marker(
    title: str,
    *,
    day: str,
    product_id: str | None = None,
) -> str | None:
    """Stable marker for one night_shift note per product per UTC day (no PASS/FAIL)."""
    t = (title or "").strip()
    if not re.search(r"night\s*shift\s*readiness", t, re.I):
        return None
    label = product_id or _project_label()
    return f"Night shift readiness {label} {day}"


def build_note_entry(
    title: str,
    bullets: list[str] | None = None,
    *,
    when: datetime | None = None,
) -> str:
    """Ad-hoc session note — Option A: fixed header, never a release ``synced`` block.

    Format::

        ## YYYY-MM-DD — {short title}

        - **When:** … UTC · … HKT
        - **Kind:** note
        - **Repo**: {_project_label()}
        - bullet...
    """
    t = (title or "").strip()
    if not t:
        raise ValueError("note title required")
    # Forbid release-like headers so freeform never looks like /sync_docs
    if re.search(r"\bsynced\b", t, re.I):
        raise ValueError(
            "ad-hoc note title must not contain 'synced' "
            "(use scripts/sync_vault_devlog.py without --note for releases)"
        )
    if re.match(r"^v?\d+\.\d+\.\d+", t, re.I):
        raise ValueError(
            "ad-hoc note title must not start with a semver release id "
            "(that shape is reserved for /sync_docs release entries)"
        )
    now = _as_utc(when)
    day = now.strftime("%Y-%m-%d")
    lines = [
        f"## {day} — {t}",
        "",
        format_when_line(now),
        "- **Kind:** note",
        f"- **Repo**: {_project_label()}",
    ]
    for b in bullets or []:
        s = str(b).strip()
        if not s:
            continue
        if s.startswith("- "):
            lines.append(s)
        else:
            lines.append(f"- {s}")
    lines.append("")
    return "\n".join(lines)


def append_note(
    vault_root: Path,
    title: str,
    bullets: list[str] | None = None,
    *,
    dry_run: bool = False,
    when: datetime | None = None,
    force: bool = False,
) -> tuple[Path, str, bool]:
    """Prepend an ad-hoc note. Returns (dev_log, entry, wrote)."""
    dev_log = vault_root / DEV_LOG_REL
    now = _as_utc(when)
    day = now.strftime("%Y-%m-%d")
    entry = build_note_entry(title, bullets, when=now)
    ns_marker = night_shift_day_marker(title, day=day, product_id=_project_label())
    if dry_run:
        return dev_log, entry, True
    if ns_marker and not force and entry_exists(dev_log, ns_marker):
        return dev_log, "", False
    prepend_entry(dev_log, entry)
    return dev_log, entry, True


def sync_vault(
    vault_root: Path,
    *,
    dry_run: bool = False,
    force: bool = False,
) -> tuple[Path, str, bool]:
    """Returns (dev_log_path, entry_text, wrote). Newest-first prepend."""
    dev_log = vault_root / DEV_LOG_REL
    tag = _git_tag()
    runbook = _parse_release_runbook(RUNBOOK_PATH)
    workflow = _parse_workflow_last_release(WORKFLOW_PATH)
    task = _pipeline_task(ROOT / ".agents" / "state" / "pipeline.json")
    shaping = parse_shaping_next()
    version = runbook.get("version") or tag
    if version == "unknown":
        version = tag
    marker = _entry_marker(tag, version)

    entry = build_entry(
        tag=tag,
        runbook=runbook,
        workflow_release=workflow,
        pipeline_task=task,
        shaping=shaping,
    )

    if dry_run:
        return dev_log, entry, True

    if not force and entry_exists(dev_log, marker):
        return dev_log, "", False

    prepend_entry(dev_log, entry)
    return dev_log, entry, True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--vault",
        type=Path,
        default=None,
        help="Optional vault root (or set PRODUCT_VAULT_ROOT; vault off if unset)",
    )
    ap.add_argument("--dry-run", action="store_true", help="Print entry without writing")
    ap.add_argument("--check", action="store_true", help="Exit 1 if current tag not logged")
    ap.add_argument("--force", action="store_true", help="Append even if marker exists")
    # Option A: ad-hoc notes (never release "synced" template)
    ap.add_argument(
        "--note",
        metavar="TITLE",
        help="Append ad-hoc session note (## YYYY-MM-DD — TITLE). Not for releases.",
    )
    ap.add_argument(
        "--bullet",
        action="append",
        default=[],
        dest="bullets",
        help="Bullet line for --note (repeatable). Prefer 'Key: value' form.",
    )
    args = ap.parse_args()

    try:
        from vault_resolve import resolve_vault_root

        resolved = resolve_vault_root(cli_vault=args.vault, product_root=ROOT, require_enabled=False)
    except Exception:
        resolved = args.vault
    if resolved is None:
        print("⚠️  VAULT SKIP: vault not configured (set PRODUCT_VAULT_ROOT or --vault; optional)", file=sys.stderr)
        return 0
    vault = Path(resolved).expanduser().resolve()
    if not vault.is_dir() and not args.dry_run:
        print(f"⚠️  VAULT SKIP: {vault} not found", file=sys.stderr)
        return 0

    # --- Ad-hoc note path (Option A) ---
    if args.note:
        try:
            dev_log, entry, wrote = append_note(
                vault,
                args.note,
                args.bullets or None,
                dry_run=args.dry_run,
                force=args.force,
            )
        except ValueError as exc:
            print(f"❌ note rejected: {exc}", file=sys.stderr)
            return 2
        except PermissionError as exc:
            print(f"⚠️  VAULT SKIP: {exc}", file=sys.stderr)
            return 0
        if args.dry_run:
            print(entry, end="" if entry.endswith("\n") else "\n")
            return 0
        if not wrote:
            print(f"⏭️  vault note skipped (dedupe or exists): {dev_log}")
            return 0
        print(f"✅ vault note prepended (newest-first): {dev_log}")
        return 0

    try:
        dev_log, entry, appended = sync_vault(vault, dry_run=args.dry_run, force=args.force)
    except PermissionError as exc:
        print(f"⚠️  VAULT SKIP: {exc}", file=sys.stderr)
        return 0

    tag = _git_tag()
    runbook = _parse_release_runbook(RUNBOOK_PATH)
    version = runbook.get("version") or tag
    marker = _entry_marker(tag, version)

    if args.check:
        if entry_exists(dev_log, marker):
            print(f"✅ vault dev-log has entry for {marker}")
            return 0
        print(f"❌ vault dev-log missing entry for {marker}", file=sys.stderr)
        return 1

    if args.dry_run:
        print(entry, end="" if entry.endswith("\n") else "\n")
        return 0

    if appended:
        print(f"✅ vault dev-log updated: {dev_log}")
    else:
        print(f"✅ vault dev-log already has {marker}: {dev_log}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
