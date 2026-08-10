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
    """Tiny subset: product_path_prefixes + smoke name/cmd/cwd + review_scope ints."""
    out: dict[str, Any] = {}
    m = re.search(
        r"^product_path_prefixes:\s*\n((?:[ \t]+-[ \t]+.+\n?)+)",
        text,
        re.MULTILINE,
    )
    if m:
        prefs = re.findall(r"^[ \t]+-[ \t]+(\S+)\s*$", m.group(1), re.MULTILINE)
        out["product_path_prefixes"] = prefs

    # review_scope: large_* integers (HSQ-1; stdlib when PyYAML absent)
    rsm = re.search(
        r"^review_scope:\s*\n(.*?)(?=^[a-zA-Z_][\w-]*:|\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    if rsm:
        rs: dict[str, Any] = {}
        for km in re.finditer(
            r"^[ \t]+(large_files|large_lines|large_non_test_loc|large_product_paths):\s*(\d+)\s*$",
            rsm.group(1),
            re.MULTILINE,
        ):
            rs[km.group(1)] = int(km.group(2))
        if rs:
            out["review_scope"] = rs

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

    # web_e2e: enabled/strict/require_s_ids + surfaces list (stdlib, no PyYAML)
    we: dict[str, Any] = {}
    wm = re.search(
        r"^web_e2e:\s*\n(.*?)(?=^[a-zA-Z_][\w-]*:|\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    if wm:
        section = wm.group(1)
        for key in ("enabled", "strict", "require_s_ids", "auto_detect"):
            key_m = re.search(rf"^[ \t]+{key}:\s*(\S+)", section, re.MULTILINE)
            if key_m:
                raw = key_m.group(1).strip().strip("'\"")
                if raw.lower() in ("true", "yes", "1"):
                    we[key] = True
                elif raw.lower() in ("false", "no", "0"):
                    we[key] = False
                else:
                    we[key] = raw
        # surfaces: remainder of web_e2e after "surfaces:" key (avoid mid-block keys)
        surfaces: list[dict[str, Any]] = []
        sm = re.search(r"^[ \t]+surfaces:\s*\n(.*)\Z", section, re.MULTILINE | re.DOTALL)
        if sm:
            body = sm.group(1)
            # Surface list items: 4-space indent "- id:" (not 8-space nested scenarios)
            parts = re.split(r"(?m)^( {4}-\s+id:\s*\S+[ \t]*\n)", body)
            if len(parts) == 1:
                # try 2-space list under surfaces
                parts = re.split(r"(?m)^( {2}-\s+id:\s*\S+[ \t]*\n)", body)
            i = 1
            while i + 1 < len(parts):
                head = parts[i]
                block = parts[i + 1]
                i += 2
                sid_m = re.search(r"id:\s*(\S+)", head)
                if not sid_m:
                    continue
                sid = sid_m.group(1).strip().strip("'\"")
                surf: dict[str, Any] = {"id": sid}
                pm = re.search(r"^[ \t]+playwright:\s*(\S+)", block, re.MULTILINE)
                if pm:
                    surf["playwright"] = pm.group(1).strip().strip("'\"")
                om = re.search(r"^[ \t]+order:\s*(\d+)", block, re.MULTILINE)
                if om:
                    surf["order"] = int(om.group(1))
                path_m = re.search(r"^[ \t]+path:\s*(\S+)", block, re.MULTILINE)
                if path_m:
                    surf["path"] = path_m.group(1).strip().strip("'\"")
                scens: list[dict[str, Any]] = []
                if re.search(r"scenarios:", block):
                    for rid in re.findall(
                        r"^[ \t]+-\s+id:\s*(\S+)",
                        block,
                        re.MULTILINE,
                    ):
                        rid = rid.strip().strip("'\"")
                        scens.append({"id": rid, "name": rid, "steps": ["open"]})
                    if not scens:
                        scens = [{"id": "smoke", "name": "smoke", "steps": ["open"]}]
                    surf["scenarios"] = scens
                if "scenarios" not in surf:
                    surf["scenarios"] = [
                        {"id": "smoke", "name": "smoke", "steps": ["open"]}
                    ]
                if "playwright" not in surf:
                    surf["playwright"] = f"e2e/{sid}.spec.ts"
                surfaces.append(surf)
        if surfaces:
            we["surfaces"] = surfaces
        elif re.search(r"^[ \t]+surfaces:\s*\[\s*\]", section, re.MULTILINE):
            we["surfaces"] = []
        if we:
            out["web_e2e"] = we
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
        if path == p or path.startswith((p + "/", pref)):
            return True
    return False
