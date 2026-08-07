#!/usr/bin/env python3
"""Strict vault layout lint — zero drift for root + 01-Projects product trees.

Reads:
  - agent-harness config/night_shift_products.yaml (product_id → repo)
  - each product ``.agents/product_plugin.yaml`` vault.project_label + vault.extra_dirs
  - optional vault-local ``agent-tasks/vault-schema.local.yaml`` (extra allowed roots)

Exit 1 if any ERROR. WARN fails by default (strict-warn).
Opt out: --no-strict-warn or VAULT_SCHEMA_STRICT_WARN=0.

Does not modify files. Safe for overnight timers.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Any

# Root directories agents/timers may create content under (plus hidden .obsidian etc.)
ROOT_ALLOW = frozenset(
    {
        "raw",
        "wiki",
        "agent-tasks",
        "00-Inbox",
        "01-Projects",
        "02-Areas",
        "03-Resources",
        "04-Archive",
        "_templates",
        "_attachments",
        # stub pointers left by hygiene (not content dumps)
        "QA",
    }
)

# Files always allowed at 01-Projects/<label>/
PROJECT_FILE_ALLOW = frozenset(
    {
        "dev-log.md",
        "night-shift-log.md",
        "TODO.md",
        "project.md",
        "decisions.md",
        "README.md",
        ".gitkeep",
    }
)

# Directories always allowed under every product
PROJECT_DIR_ALLOW = frozenset({"docs", "_archive"})

# Multi-product ops re-homed to agent-tasks/night-shift/ (2026-08-07).
# No special 01-Projects folder.
SPECIAL_PROJECTS: dict[str, set[str]] = {}


def _load_yamlish_list_block(text: str, key: str) -> list[str]:
    """Extract simple YAML list under vault.extra_dirs or top-level key."""
    # vault: section extra_dirs
    m = re.search(
        rf"(?ms)^[ \t]+{re.escape(key)}:\s*\n((?:[ \t]+-[ \t]+.+\n?)*)",
        text,
    )
    if not m:
        m = re.search(
            rf"(?ms)^{re.escape(key)}:\s*\n((?:[ \t]+-[ \t]+.+\n?)*)",
            text,
        )
    if not m:
        return []
    return re.findall(r"^[ \t]+-[ \t]+(\S+)\s*$", m.group(1), re.MULTILINE)


def _vault_scalar(text: str, key: str) -> str:
    m = re.search(rf"(?m)^[ \t]+{re.escape(key)}:\s*[\"']?([^\s\"'#]+)", text)
    if m:
        return m.group(1).strip()
    m = re.search(rf"(?m)^{re.escape(key)}:\s*[\"']?([^\s\"'#]+)", text)
    return m.group(1).strip() if m else ""


def load_plugin_vault(product_root: Path) -> dict[str, Any]:
    path = product_root / ".agents" / "product_plugin.yaml"
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8", errors="replace")
    label = _vault_scalar(text, "project_label") or _vault_scalar(text, "product_id")
    extra = _load_yamlish_list_block(text, "extra_dirs")
    # also try product_id at top
    pid = _vault_scalar(text, "product_id")
    return {
        "product_id": pid,
        "project_label": label or pid,
        "extra_dirs": [e.strip().strip("\"'") for e in extra if e.strip()],
        "plugin_path": str(path),
    }


def load_night_shift_products(path: Path) -> dict[str, Path]:
    if not path.is_file():
        return {}
    out: dict[str, Path] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        pid, proot = line.split(":", 1)
        pid = pid.strip()
        proot = proot.strip().strip("\"'")
        p = Path(proot).expanduser()
        if p.is_dir():
            out[pid] = p
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--vault", type=Path, required=True)
    ap.add_argument(
        "--products-file",
        type=Path,
        default=None,
        help="night_shift_products.yaml (default: agent-harness config)",
    )
    ap.add_argument(
        "--report",
        type=Path,
        default=None,
        help="Write markdown report (default: agent-tasks/schema-lint-report.md)",
    )
    ap.add_argument(
        "--strict-warn",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="WARN counts as fail (default: on; disable with --no-strict-warn or VAULT_SCHEMA_STRICT_WARN=0)",
    )
    args = ap.parse_args()
    if args.strict_warn is None:
        env = (os.environ.get("VAULT_SCHEMA_STRICT_WARN") or "1").strip().lower()
        args.strict_warn = env not in ("0", "false", "off", "no")
    vault = args.vault.expanduser().resolve()
    if not vault.is_dir():
        print(f"ERROR vault missing: {vault}", file=sys.stderr)
        return 2

    home = Path.home()
    products_file = args.products_file or Path(
        os.environ.get(
            "NIGHT_SHIFT_PRODUCTS_FILE",
            str(home / "agent-harness" / "config" / "night_shift_products.yaml"),
        )
    )
    products = load_night_shift_products(products_file)

    errors: list[str] = []
    warns: list[str] = []

    # --- Root allowlist ---
    for child in sorted(vault.iterdir()):
        name = child.name
        if name.startswith("."):
            continue  # .obsidian, .stfolder, .stversions, …
        if name not in ROOT_ALLOW:
            errors.append(f"root forbidden entry: {name}/ (not in schema ROOT_ALLOW)")

    # --- Build expected project labels from plugins ---
    label_to_extra: dict[str, set[str]] = {}
    label_to_pid: dict[str, str] = {}
    for pid, proot in products.items():
        cfg = load_plugin_vault(proot)
        label = (cfg.get("project_label") or pid).strip()
        if not label:
            errors.append(f"product {pid}: missing project_label in plugin")
            continue
        extras = set(cfg.get("extra_dirs") or [])
        label_to_extra[label] = extras
        label_to_pid[label] = pid
        # check declared paths exist in plugin consistency
        if label != pid and pid not in label:
            warns.append(
                f"product {pid}: project_label={label!r} differs from product_id "
                f"(ok if intentional; folder is 01-Projects/{label}/)"
            )

    projects_root = vault / "01-Projects"
    if projects_root.is_dir():
        for pdir in sorted(projects_root.iterdir()):
            if not pdir.is_dir() or pdir.name.startswith("."):
                continue
            label = pdir.name
            # special multi-product ops
            if label in SPECIAL_PROJECTS:
                allow_files = SPECIAL_PROJECTS[label]
                for child in pdir.iterdir():
                    if child.name.startswith("."):
                        continue
                    if child.is_dir():
                        errors.append(
                            f"01-Projects/{label}/: unexpected dir {child.name}/ "
                            f"(special project allows files only: {sorted(allow_files)})"
                        )
                    elif child.name not in allow_files:
                        warns.append(
                            f"01-Projects/{label}/: undeclared file {child.name}"
                        )
                continue

            if label not in label_to_extra and label not in label_to_pid:
                # folder without registered product
                errors.append(
                    f"01-Projects/{label}/: no product_plugin registration "
                    f"(not in {products_file.name} / project_label)"
                )
                continue

            extras = label_to_extra.get(label, set())
            allowed_dirs = PROJECT_DIR_ALLOW | extras

            for child in sorted(pdir.iterdir()):
                if child.name.startswith("."):
                    continue
                if child.is_dir():
                    if child.name not in allowed_dirs:
                        errors.append(
                            f"01-Projects/{label}/{child.name}/: undeclared directory "
                            f"(add to vault.extra_dirs in product_plugin or remove). "
                            f"allowed={sorted(allowed_dirs)}"
                        )
                else:
                    if child.name in PROJECT_FILE_ALLOW:
                        continue
                    # loose reports etc.
                    warns.append(
                        f"01-Projects/{label}/{child.name}: loose file "
                        f"(prefer docs/ or _archive/reports/)"
                    )

            # required files soft-check
            for req in ("dev-log.md", "night-shift-log.md"):
                if not (pdir / req).is_file() and label in label_to_pid:
                    warns.append(f"01-Projects/{label}/: missing recommended {req}")

    # registered product with no vault folder yet — warn only
    for label, pid in label_to_pid.items():
        if not (projects_root / label).is_dir():
            warns.append(
                f"product {pid}: no vault folder 01-Projects/{label}/ yet "
                f"(created on first sync_docs/night_shift)"
            )

    report = args.report or (vault / "agent-tasks" / "schema-lint-report.md")
    report.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Vault schema lint",
        "",
        f"**Vault**: `{vault}`",
        f"**Products file**: `{products_file}`",
        f"**Errors**: {len(errors)}",
        f"**Warnings**: {len(warns)}",
        "",
        "## Errors",
        "",
    ]
    if errors:
        for e in errors:
            lines.append(f"- ❌ {e}")
    else:
        lines.append("_None._")
    lines += ["", "## Warnings", ""]
    if warns:
        for w in warns:
            lines.append(f"- ⚠️ {w}")
    else:
        lines.append("_None._")
    lines += [
        "",
        "## Schema (summary)",
        "",
        "- Root allow: " + ", ".join(sorted(ROOT_ALLOW)),
        "- Project always dirs: " + ", ".join(sorted(PROJECT_DIR_ALLOW)),
        "- Project always files: " + ", ".join(sorted(PROJECT_FILE_ALLOW)),
        "- Per-product extras from `vault.extra_dirs` in product_plugin.yaml",
        "",
    ]
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {report}")

    for e in errors:
        print(f"ERROR  {e}", file=sys.stderr)
    for w in warns:
        print(f"WARN   {w}", file=sys.stderr)
    print(f"schema-lint: {len(errors)} error(s), {len(warns)} warning(s)")

    if errors:
        return 1
    if args.strict_warn and warns:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
