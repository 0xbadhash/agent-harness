#!/usr/bin/env python3
"""Resolve optional knowledge-vault path. Vault is never required by default.

Single resolver SoT (Option B). Order:
  1. CLI --vault if provided by caller
  2. PRODUCT_VAULT_ROOT (canonical env for all products)
  3. Env named by product_plugin.vault.root_env (if different from canonical)
  4. product_plugin.vault.default_root if non-empty
  5. None → vault steps skipped

Legacy multi-env aliases (WATCHLIST_VAULT_ROOT, etc.) are **removed** —
set PRODUCT_VAULT_ROOT only.

Does not hardcode /opt/second-brain or any host path (defaults come from plugin).
"""
from __future__ import annotations

import os
import re
from pathlib import Path

# Canonical only (no legacy aliases)
CANONICAL_VAULT_ENV = "PRODUCT_VAULT_ROOT"
LEGACY_VAULT_ENVS: tuple[str, ...] = ()  # intentionally empty


def load_vault_config(product_root: Path | None = None) -> dict:
    root = product_root or Path.cwd()
    plugin = root / ".agents" / "product_plugin.yaml"
    cfg: dict = {
        "enabled": False,
        "root_env": CANONICAL_VAULT_ENV,
        "default_root": "",
        "project_label": "product",
        "dev_log_rel": "",
        "product_id": "",
        "mirror_docs": [],
        "extra_dirs": [],
    }
    if not plugin.is_file():
        return cfg
    text = plugin.read_text(encoding="utf-8")
    # enabled
    m = re.search(r"^\s*enabled:\s*(true|false|yes|no|1|0)\s*$", text, re.M | re.I)
    if m:
        cfg["enabled"] = m.group(1).lower() in ("true", "yes", "1")
    # simple keys
    for key in ("root_env", "default_root", "project_label", "dev_log_rel", "product_id"):
        m = re.search(rf"^\s*{key}:\s*(.+)$", text, re.M)
        if m:
            val = m.group(1).strip().strip("\"'")
            # strip inline comments
            if " #" in val:
                val = val.split(" #", 1)[0].rstrip()
            if key == "product_id":
                cfg["product_id"] = val
                if cfg["project_label"] == "product":
                    cfg["project_label"] = val
            else:
                cfg[key] = val
    # extra_dirs list under vault:
    block = re.search(
        r"(?ms)^[ \t]+extra_dirs:\s*\n((?:[ \t]+-[ \t]+.+\n?)*)",
        text,
    )
    if block:
        cfg["extra_dirs"] = [
            e.strip().strip("\"'")
            for e in re.findall(r"^[ \t]+-[ \t]+(\S+)\s*$", block.group(1), re.M)
            if e.strip()
        ]
    # mirror_docs list under vault:
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
    if mirrors:
        cfg["mirror_docs"] = mirrors
    if not cfg["dev_log_rel"] and cfg["project_label"]:
        cfg["dev_log_rel"] = f"01-Projects/{cfg['project_label']}/dev-log.md"
    return cfg


def project_rel(product_root: Path | None = None, *parts: str) -> Path:
    """Relative path under 01-Projects/<label>/… from plugin."""
    cfg = load_vault_config(product_root)
    label = (cfg.get("project_label") or cfg.get("product_id") or "product").strip()
    return Path("01-Projects") / label / Path(*parts) if parts else Path("01-Projects") / label


def resolve_vault_root(
    *,
    cli_vault: Path | str | None = None,
    product_root: Path | None = None,
    require_enabled: bool = True,
) -> Path | None:
    """Return vault Path or None if vault integration is off / unset."""
    cfg = load_vault_config(product_root)
    if require_enabled and not cfg.get("enabled"):
        # Explicit CLI vault still allowed (operator override)
        if cli_vault:
            return Path(str(cli_vault)).expanduser()
        # Plugins that omit `enabled:` but declare default_root still resolve
        if not (cfg.get("default_root") or "").strip():
            return None

    if cli_vault:
        return Path(str(cli_vault)).expanduser()

    # 1) Canonical env first
    canon = os.environ.get(CANONICAL_VAULT_ENV, "").strip()
    if canon:
        return Path(canon).expanduser()

    # 2) Plugin-declared root_env only if still set to a custom name
    env_name = (cfg.get("root_env") or CANONICAL_VAULT_ENV).strip()
    if env_name and env_name != CANONICAL_VAULT_ENV:
        env_val = os.environ.get(env_name, "").strip()
        if env_val:
            return Path(env_val).expanduser()

    default = (cfg.get("default_root") or "").strip()
    if default:
        return Path(default).expanduser()

    return None
