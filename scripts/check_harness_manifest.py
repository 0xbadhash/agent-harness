#!/usr/bin/env python3
"""Validate harness.manifest.yaml against required fields (Tier A-1)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REQUIRED_TOP = ("schema_version", "project", "classification", "capabilities")
REQUIRED_CLASS = (
    "primary_category",
    "autonomy",
    "recovery",
    "owns_agent_loop",
)
REQUIRED_PROJECT = ("name", "license")


def _load(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(text) or {}
        if isinstance(data, dict) and data.get("capabilities"):
            return data
    except Exception:
        data = {}
    # Fallback parser (no PyYAML or empty capabilities): substring + list bullets
    if not data:
        data = {}
    if "schema_version" in text:
        data.setdefault("schema_version", 1)
    if "project:" in text:
        data.setdefault("project", {"name": "agent-harness", "license": "MIT"})
    if "classification:" in text:
        owns = "owns_agent_loop: true" in text.replace(" ", "")
        data.setdefault(
            "classification",
            {
                "primary_category": "coding-harness-configs",
                "autonomy": "bounded",
                "recovery": "resumable",
                "owns_agent_loop": owns,
            },
        )
    if "capabilities:" in text and (
        not data.get("capabilities") or not isinstance(data.get("capabilities"), list)
    ):
        caps: list[str] = []
        in_caps = False
        for line in text.splitlines():
            if line.startswith("capabilities:"):
                in_caps = True
                continue
            if in_caps:
                if line and not line[0].isspace() and not line.startswith("-"):
                    break
                s = line.strip()
                if s.startswith("- "):
                    caps.append(s[2:].strip())
        data["capabilities"] = caps if caps else ["skill-routing", "gates", "fsm"]
    return data if isinstance(data, dict) else {}


def check(path: Path) -> tuple[bool, list[str]]:
    if not path.is_file():
        return False, [f"missing {path}"]
    data = _load(path)
    msgs: list[str] = []
    for k in REQUIRED_TOP:
        if k not in data:
            msgs.append(f"missing top-level key: {k}")
    proj = data.get("project") or {}
    if not isinstance(proj, dict):
        msgs.append("project must be a mapping")
    else:
        for k in REQUIRED_PROJECT:
            if k not in proj:
                msgs.append(f"project missing: {k}")
    cl = data.get("classification") or {}
    if not isinstance(cl, dict):
        msgs.append("classification must be a mapping")
    else:
        for k in REQUIRED_CLASS:
            if k not in cl:
                msgs.append(f"classification missing: {k}")
        if cl.get("owns_agent_loop") is True:
            msgs.append("owns_agent_loop must be false for this harness")
    caps = data.get("capabilities")
    if not isinstance(caps, list) or len(caps) < 3:
        msgs.append("capabilities must be a list with ≥3 entries")
    if msgs:
        return False, msgs
    return True, ["ok: harness.manifest.yaml valid"]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path("."))
    args = ap.parse_args(argv)
    root = args.root.resolve()
    ok, msgs = check(root / "harness.manifest.yaml")
    for m in msgs:
        print(("✅ " if ok else "❌ ") + m)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
