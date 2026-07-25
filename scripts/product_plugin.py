#!/usr/bin/env python3
"""Load `.agents/product_plugin.yaml` — stack-agnostic product config."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore


def plugin_path(product_root: Path) -> Path:
    return product_root / ".agents" / "product_plugin.yaml"


def load_plugin(product_root: Path) -> dict[str, Any]:
    """Return plugin dict or {} if missing/unreadable."""
    path = plugin_path(product_root)
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8")
    if yaml is not None:
        data = yaml.safe_load(text) or {}
        return data if isinstance(data, dict) else {}
    # Minimal fallback without PyYAML (stdlib only)
    return _parse_minimal_plugin(text)


def _parse_minimal_plugin(text: str) -> dict[str, Any]:
    """Tiny subset: product_path_prefixes + smoke name/cmd/cwd."""
    out: dict[str, Any] = {}
    m = re.search(
        r"^product_path_prefixes:\s*\n((?:[ \t]+-[ \t]+.+\n?)+)",
        text,
        re.MULTILINE,
    )
    if m:
        prefs = re.findall(r"^[ \t]+-[ \t]+(\S+)\s*$", m.group(1), re.MULTILINE)
        out["product_path_prefixes"] = prefs

    # smoke: section — each list item starts with "- name:" (stdlib, no PyYAML)
    # Prefer section-scoped split so multi-entry smoke lists all parse (not only first).
    smoke: list[dict[str, Any]] = []
    sm = re.search(
        r"^smoke:\s*\n(.*?)(?=^[a-zA-Z_][\w-]*:|\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    if sm:
        section = sm.group(1)
        parts = re.split(r"(?m)^([ \t]+-[ \t]+name:\s*\S+[ \t]*\n)", section)
        i = 1
        while i + 1 < len(parts):
            head = parts[i]
            body = parts[i + 1]
            i += 2
            nm = re.search(r"name:\s*(\S+)", head)
            if not nm:
                continue
            name = nm.group(1).strip().strip("'\"")
            cmd_m = re.search(r"cmd:\s*\[([^\]]*)\]", body)
            if not cmd_m:
                continue
            argv = [
                p.strip().strip("'\"") for p in cmd_m.group(1).split(",") if p.strip()
            ]
            entry: dict[str, Any] = {"name": name, "cmd": argv}
            cwd_m = re.search(r"cwd:\s*(\S+)", body)
            if cwd_m:
                entry["cwd"] = cwd_m.group(1).strip().strip("'\"")
            smoke.append(entry)
    if smoke:
        out["smoke"] = smoke
    return out


def load_product_path_prefixes(product_root: Path) -> list[str]:
    data = load_plugin(product_root)
    raw = data.get("product_path_prefixes") or []
    if not isinstance(raw, list):
        return []
    return [str(p).strip() for p in raw if str(p).strip()]


def path_matches_product_prefixes(path: str, prefixes: list[str]) -> bool:
    path = path.lstrip("./")
    for pref in prefixes:
        p = pref.rstrip("/")
        if path == p or path.startswith(p + "/") or path.startswith(pref):
            return True
    return False
