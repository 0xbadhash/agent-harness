#!/usr/bin/env python3
"""Resolve optional knowledge-vault path. Vault is never required by default.

Order:
  1. CLI --vault if provided by caller
  2. Env named by product_plugin.vault.root_env (default PRODUCT_VAULT_ROOT)
  3. product_plugin.vault.default_root if non-empty
  4. None → vault steps skipped

Does not hardcode /opt/second-brain or any host path.
"""
from __future__ import annotations

import os
import re
from pathlib import Path


def load_vault_config(product_root: Path | None = None) -> dict:
    root = product_root or Path.cwd()
    plugin = root / ".agents" / "product_plugin.yaml"
    cfg = {
        "enabled": False,
        "root_env": "PRODUCT_VAULT_ROOT",
        "default_root": "",
        "project_label": "product",
        "dev_log_rel": "",
        "mirror_docs": [],
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
            if key == "product_id" and cfg["project_label"] == "product":
                cfg["project_label"] = val
            elif key != "product_id":
                cfg[key] = val
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
            p = Path(str(cli_vault)).expanduser()
            return p if p.is_dir() or not p.exists() else p
        return None

    if cli_vault:
        return Path(str(cli_vault)).expanduser()

    env_name = cfg.get("root_env") or "PRODUCT_VAULT_ROOT"
    env_val = os.environ.get(env_name, "").strip()
    if env_val:
        return Path(env_val).expanduser()

    # Common alias env vars (still no hardcoded host path)
    for alt in ("PRODUCT_VAULT_ROOT", "SECOND_BRAIN_VAULT", "VAULT_ROOT"):
        v = os.environ.get(alt, "").strip()
        if v:
            return Path(v).expanduser()

    default = (cfg.get("default_root") or "").strip()
    if default:
        return Path(default).expanduser()

    return None
