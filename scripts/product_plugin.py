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

    # smoke entries: blocks starting with "  - name:"
    smoke: list[dict[str, Any]] = []
    for block in re.finditer(
        r"^[ \t]+-[ \t]+name:\s*(\S+)\s*\n"
        r"((?:[ \t]+.+\n?)*)",
        text,
        re.MULTILINE,
    ):
        # Only under smoke: section — approximate by requiring cmd line in block
        name = block.group(1).strip().strip("'\"")
        body = block.group(2)
        cmd_m = re.search(r"cmd:\s*\[([^\]]*)\]", body)
        if not cmd_m:
            continue
        # Only accept if we're after a "smoke:" header somewhere before
        pos = block.start()
        before = text[:pos]
        if not re.search(r"^smoke:\s*$", before, re.MULTILINE):
            # still allow if 'smoke:' appears earlier
            if "smoke:" not in before:
                continue
        parts = [p.strip().strip("'\"") for p in cmd_m.group(1).split(",") if p.strip()]
        entry: dict[str, Any] = {"name": name, "cmd": parts}
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
