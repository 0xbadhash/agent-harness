#!/usr/bin/env python3
"""Full post-release doc sync: repo workflow + vault mirrors + release dev-log.

Called by ``/sync_docs`` after ship. Complements ``sync_vault_devlog.py`` (release
entry only) by:

1. Updating ``WORKFLOW_DOCUMENTATION.md`` (Last Release, phase, drift row)
2. Stamping ``docs/PRODUCT.md`` / ``README.md`` current-release lines when markers exist
3. Mirroring product docs into the Obsidian vault project tree
4. Refreshing ``wiki/{project_label}.md`` index (latest tag + mirror table)
5. Appending the structured vault release entry via ``sync_vault_devlog``

Does **not** invent product feature docs. Mirrors are copies of repo truth.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
DEFAULT_VAULT = None


def _project_label() -> str:
    try:
        sys.path.insert(0, str(SCRIPTS))
        from vault_resolve import load_vault_config

        return load_vault_config(ROOT).get("project_label") or "product"
    except Exception:
        return "product"
  # optional; use PRODUCT_VAULT_ROOT or --vault

# Default mirrors when product_plugin.vault.mirror_docs is absent
DEFAULT_MIRRORS = [
    "docs/PRODUCT.md",
    "docs/PRODUCT_BOUNDARY.md",
    "docs/ARCHITECTURE.md",
    "docs/GRAPHIFY.md",
    "docs/SECURITY.md",
    "docs/TESTING.md",
    "RELEASE_RUNBOOK.md",
    "PR_DRAFT.md",
]

WORKFLOW_PATH = ROOT / "WORKFLOW_DOCUMENTATION.md"
PRODUCT_MD = ROOT / "docs" / "PRODUCT.md"
README_PATH = ROOT / "README.md"


def _git_tag(cwd: Path = ROOT) -> str:
    r = subprocess.run(
        ["git", "describe", "--tags", "--abbrev=0"],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    return r.stdout.strip() if r.returncode == 0 and r.stdout.strip() else "unknown"


def _git_head_short(cwd: Path = ROOT) -> str:
    r = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    return r.stdout.strip() if r.returncode == 0 else ""


def _load_plugin_mirrors() -> list[str]:
    plugin = ROOT / ".agents" / "product_plugin.yaml"
    if not plugin.is_file():
        return list(DEFAULT_MIRRORS)
    text = plugin.read_text(encoding="utf-8")
    # minimal YAML parse for vault.mirror_docs list
    in_vault = False
    in_mirrors = False
    mirrors: list[str] = []
    for line in text.splitlines():
        if re.match(r"^vault:\s*$", line):
            in_vault = True
            in_mirrors = False
            continue
        if in_vault and re.match(r"^[a-zA-Z_]", line) and not line.startswith(" "):
            break
        if in_vault and re.match(r"^\s+mirror_docs:\s*$", line):
            in_mirrors = True
            continue
        if in_mirrors:
            m = re.match(r"^\s+-\s+(.+)$", line)
            if m:
                mirrors.append(m.group(1).strip().strip("\"'"))
            elif re.match(r"^\s+[a-zA-Z_]", line):
                in_mirrors = False
    return mirrors or list(DEFAULT_MIRRORS)


def _runbook_scope() -> str:
    sys.path.insert(0, str(SCRIPTS))
    import sync_vault_devlog as svd  # type: ignore

    rb = svd._parse_release_runbook(ROOT / "RELEASE_RUNBOOK.md")
    scope = (rb.get("scope") or rb.get("theme") or "").strip()
    if not scope:
        # first summary bullet
        text = (ROOT / "RELEASE_RUNBOOK.md").read_text(encoding="utf-8") if (
            ROOT / "RELEASE_RUNBOOK.md"
        ).is_file() else ""
        m = re.search(r"## (?:Summary|Changes)\s*\n+((?:[-*].+\n?)+)", text)
        if m:
            first = m.group(1).strip().splitlines()[0]
            scope = re.sub(r"^[-*]\s+", "", first).strip()
    return scope or "see RELEASE_RUNBOOK.md"


def update_workflow(
    path: Path,
    *,
    version: str,
    scope: str,
    score: int = 100,
    dry_run: bool = False,
) -> str:
    """Rewrite Current State Last Release + prepend drift row for this ship."""
    if not path.is_file():
        return "workflow: missing (skip)"
    text = path.read_text(encoding="utf-8")
    release_line = f"- **Last Release:** `{version}` — {scope}"
    text2 = re.sub(
        r"- \*\*Last Release:\*\*.*",
        release_line,
        text,
        count=1,
    )
    text2 = re.sub(
        r"- \*\*Pipeline Phase:\*\*.*",
        "- **Pipeline Phase:** `init`",
        text2,
        count=1,
    )
    text2 = re.sub(
        r"- \*\*Review Score:\*\*.*",
        f"- **Review Score:** {score}",
        text2,
        count=1,
    )
    text2 = re.sub(
        r"- \*\*In progress:\*\*.*",
        "- **In progress:** — ready for next cycle after `/sync_docs`",
        text2,
        count=1,
    )

    drift_id = re.sub(r"[^A-Z0-9]+", "-", version.upper()).strip("-")[:24] or "REL"
    row = (
        f"| {drift_id} | Low | release | Full doc sync (repo workflow + vault mirrors) "
        f"| Shipped {version} |\n"
    )
    if f"Shipped {version}" not in text2:
        # insert after table header separator
        text2 = re.sub(
            r"(\|----\|[^\n]+\n)",
            r"\1" + row,
            text2,
            count=1,
        )

    if dry_run:
        return "workflow: would update"
    path.write_text(text2, encoding="utf-8")
    return f"workflow: updated Last Release → {version}"


def stamp_current_release(path: Path, version: str, *, dry_run: bool = False) -> str:
    """Update `<!-- CURRENT_RELEASE -->…<!-- /CURRENT_RELEASE -->` or create under title."""
    if not path.is_file():
        return f"{path.name}: missing (skip)"
    text = path.read_text(encoding="utf-8")
    stamp = (
        f"<!-- CURRENT_RELEASE -->\n"
        f"**Current release:** `{version}` "
        f"(docs synced via `/sync_docs`)\n"
        f"<!-- /CURRENT_RELEASE -->\n"
    )
    if "<!-- CURRENT_RELEASE -->" in text:
        text2 = re.sub(
            r"<!-- CURRENT_RELEASE -->.*?<!-- /CURRENT_RELEASE -->\n?",
            stamp,
            text,
            count=1,
            flags=re.DOTALL,
        )
    else:
        # after first H1
        text2 = re.sub(
            r"(^# .+\n)",
            r"\1\n" + stamp + "\n",
            text,
            count=1,
            flags=re.MULTILINE,
        )
    if dry_run:
        return f"{path.name}: would stamp {version}"
    path.write_text(text2, encoding="utf-8")
    return f"{path.name}: stamped {version}"


def mirror_to_vault(
    vault: Path,
    rel_paths: list[str],
    *,
    version: str,
    project_label: str = "product",
    dry_run: bool = False,
) -> list[str]:
    """Copy repo docs → vault/01-Projects/<label>/docs/ with sync banner."""
    when = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    head = _git_head_short()
    dest_root = vault / "01-Projects" / project_label / "docs"
    notes: list[str] = []
    if dry_run:
        return [f"mirror dry-run: {len(rel_paths)} files → {dest_root}"]

    dest_root.mkdir(parents=True, exist_ok=True)
    for rel in rel_paths:
        src = ROOT / rel
        if not src.is_file():
            notes.append(f"mirror skip missing: {rel}")
            continue
        # flatten: docs/PRODUCT.md → PRODUCT.md; RELEASE_RUNBOOK.md stays
        name = src.name
        dest = dest_root / name
        body = src.read_text(encoding="utf-8")
        banner = (
            f"<!-- synced-from-repo: {project_label} {version} @{head} at {when} "
            f"source={rel} — edit the git repo, not this copy -->\n\n"
        )
        # strip prior banner if re-sync
        body = re.sub(
            r"^<!-- synced-from-repo:.*?-->\n\n",
            "",
            body,
            count=1,
            flags=re.DOTALL,
        )
        dest.write_text(banner + body, encoding="utf-8")
        notes.append(f"mirror ok: {rel} → {dest.relative_to(vault)}")
    return notes


def update_wiki_index(
    vault: Path,
    *,
    version: str,
    scope: str,
    mirrored: list[str],
    project_label: str = "product",
    dry_run: bool = False,
) -> str:
    wiki = vault / "wiki" / f"{project_label}.md"
    when = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    clean = []
    for m in mirrored:
        if m.startswith("mirror ok:"):
            # "mirror ok: docs/X → 01-Projects/.../X"
            part = m.split("mirror ok:", 1)[-1].strip()
            clean.append(f"- `{part}`")
    mirror_lines = "\n".join(clean) or "- _(none this run)_"
    block = f"""---
tags:
  - type/project
  - domain/ops
---
# {project_label}

Dev logging for **{project_label}** lives under `01-Projects/{project_label}/`.

## Latest release

- **Tag:** `{version}`
- **Synced:** {when} (via `/sync_docs` full sync)
- **Scope:** {scope}

## Vault paths

| Path | Purpose |
|------|---------|
| `01-Projects/{project_label}/dev-log.md` | Append-only dev session log |
| `01-Projects/{project_label}/docs/` | Mirrored product docs from git (read-only) |
| `wiki/{project_label}.md` | This index page |

## Mirrored docs (this sync)

{mirror_lines}

## Integration

- Vault is **optional** (set `PRODUCT_VAULT_ROOT` or `vault.enabled` in product_plugin).
- Skills/policies SoT: **agent-harness** (reinstall into product).
- Full sync: `python3 scripts/sync_docs_full.py` (use `--skip-vault` when no vault).

## Related

- agent-harness `docs/source-of-truth.md`
- agent-harness `docs/second-brain-optional.md`
"""
    if dry_run:
        return "wiki: would update"
    wiki.parent.mkdir(parents=True, exist_ok=True)
    wiki.write_text(block, encoding="utf-8")
    return f"wiki: updated {wiki}"


def run_release_devlog(vault: Path, *, dry_run: bool = False, force: bool = False) -> str:
    cmd = [
        sys.executable,
        str(SCRIPTS / "sync_vault_devlog.py"),
        "--vault",
        str(vault),
    ]
    if dry_run:
        cmd.append("--dry-run")
    if force:
        cmd.append("--force")
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False)
    out = (r.stdout or "") + (r.stderr or "")
    return out.strip() or f"devlog exit={r.returncode}"


def run_full_sync(
    *,
    vault: Path | None,
    dry_run: bool = False,
    force_devlog: bool = False,
    skip_vault: bool = False,
    skip_repo: bool = False,
) -> int:
    version = _git_tag()
    scope = _runbook_scope()
    notes: list[str] = []

    if not skip_repo:
        notes.append(
            update_workflow(
                WORKFLOW_PATH, version=version, scope=scope, dry_run=dry_run
            )
        )
        notes.append(stamp_current_release(PRODUCT_MD, version, dry_run=dry_run))
        notes.append(stamp_current_release(README_PATH, version, dry_run=dry_run))

    if not skip_vault:
        if vault is None:
            print("⚠️  VAULT SKIP: no vault path resolved", file=sys.stderr)
            notes.append("vault: skipped (no path)")
        elif not vault.is_dir() and not dry_run:
            print(f"⚠️  VAULT SKIP: {vault} not found", file=sys.stderr)
            notes.append(f"vault: skipped (missing {vault})")
        else:
            vault_path: Path = vault
            mirrors = _load_plugin_mirrors()
            try:
                mnotes = mirror_to_vault(
                    vault_path,
                    mirrors,
                    version=version,
                    project_label=_project_label(),
                    dry_run=dry_run,
                )
                notes.extend(mnotes)
                notes.append(
                    update_wiki_index(
                        vault_path,
                        version=version,
                        scope=scope,
                        mirrored=mnotes,
                        project_label=_project_label(),
                        dry_run=dry_run,
                    )
                )
                notes.append(
                    run_release_devlog(
                        vault_path, dry_run=dry_run, force=force_devlog
                    )
                )
            except PermissionError as exc:
                notes.append(f"⚠️ VAULT SKIP: {exc}")
                print(f"⚠️  VAULT SKIP: {exc}", file=sys.stderr)

    for n in notes:
        print(n)
    print(f"✅ sync_docs_full complete ({version})")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--vault",
        type=Path,
        default=None,
        help="Optional vault root; default off unless PRODUCT_VAULT_ROOT / plugin enabled",
    )
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force-devlog", action="store_true", help="Force release entry append")
    ap.add_argument("--skip-vault", action="store_true")
    ap.add_argument("--skip-repo", action="store_true")
    args = ap.parse_args()
    vault = args.vault
    skip_vault = args.skip_vault
    if vault is not None:
        vault = vault.expanduser().resolve()
    else:
        try:
            sys.path.insert(0, str(SCRIPTS))
            from vault_resolve import resolve_vault_root

            vault = resolve_vault_root(product_root=ROOT, require_enabled=True)
        except Exception:
            vault = None
        if vault is None:
            skip_vault = True
            vault = Path(".")  # unused when skip_vault
        else:
            vault = Path(vault).expanduser().resolve()
    return run_full_sync(
        vault=vault,
        dry_run=args.dry_run,
        force_devlog=args.force_devlog,
        skip_vault=skip_vault,
        skip_repo=args.skip_repo,
    )


if __name__ == "__main__":
    sys.exit(main())
