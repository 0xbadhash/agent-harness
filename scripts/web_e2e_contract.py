#!/usr/bin/env python3
"""Web E2E + Comet scenario contract: detect website, validate artifacts, allocate S-ids."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from product_plugin import load_plugin

# Any one of these pairs is enough for a "human/agent scenario doc"
COMET_MARKERS_ANY = (
    "PROMPT FOR COMET",
    "Report template",
    "PASS|FAIL",
    "PASS / FAIL",
    "scenario",
)
DEFAULT_COMET = "docs/E2E_COMET_SCENARIOS.md"
DEFAULT_COMET_CANDIDATES = (
    "docs/E2E_COMET_SCENARIOS.md",
    "docs/E2E_TEST_SCENARIOS.md",
    "docs/E2E_SCENARIOS.md",
)
DEFAULT_E2E_DIR = "e2e"
DEFAULT_E2E_DIRS = ("e2e", "app/e2e", "tests/e2e")
DEFAULT_PW_CONFIGS = (
    "playwright.config.ts",
    "playwright.config.js",
    "playwright.config.mjs",
    "app/playwright.config.ts",
)


def _as_dict(x: Any) -> dict[str, Any]:
    return x if isinstance(x, dict) else {}


def detect_website(root: Path, plugin: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return {has_website, reasons[], web_e2e config}."""
    plugin = plugin if plugin is not None else load_plugin(root)
    cfg = _as_dict(plugin.get("web_e2e"))
    reasons: list[str] = []

    if cfg.get("enabled") is True:
        return {"has_website": True, "reasons": ["web_e2e.enabled=true"], "web_e2e": cfg}
    if cfg.get("enabled") is False:
        return {"has_website": False, "reasons": ["web_e2e.enabled=false"], "web_e2e": cfg}

    # enabled unset → auto-detect filesystem (and honor explicit surfaces/base_url)
    reasons = []
    if (root / "web").is_dir():
        reasons.append("web/")
    if (root / "index.html").is_file():
        reasons.append("index.html")
    if (root / "public" / "index.html").is_file():
        reasons.append("public/index.html")
    if (root / "app" / "web").is_dir():
        reasons.append("app/web/")
    if any((root / name).is_file() for name in DEFAULT_PW_CONFIGS):
        reasons.append("playwright.config")
    for ed in DEFAULT_E2E_DIRS:
        e2e = root / ed
        if e2e.is_dir() and list(e2e.glob("**/*.{spec,test}.ts")) + list(
            e2e.glob("**/*spec.ts")
        ):
            reasons.append(f"{ed}/*.spec.ts")
            break
    for cand in DEFAULT_COMET_CANDIDATES:
        if (root / cand).is_file():
            reasons.append(cand)
            break
    docs = root / "docs"
    if docs.is_dir() and (
        list(docs.glob("*COMET*"))
        or list(docs.glob("*E2E*SCENARIO*"))
        or list(docs.glob("E2E*.md"))
    ):
        if not any(r.startswith("docs/") for r in reasons):
            reasons.append("docs/E2E*")

    if cfg.get("surfaces") or cfg.get("base_url"):
        reasons.append("web_e2e.surfaces|base_url")

    auto = cfg.get("auto_detect", True)
    has = bool(reasons) if auto else bool(cfg.get("surfaces") or cfg.get("base_url"))
    return {"has_website": has, "reasons": reasons, "web_e2e": cfg}


def allocate_scenario_ids(surfaces: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Deterministic S0..Sn assignment by surface order then scenario list order.
    Returns flat list of {global_id, surface_id, local_id, name, steps, playwright, path}.
    """
    ordered = sorted(
        surfaces,
        key=lambda s: (int(s.get("order", 1000)), str(s.get("id", ""))),
    )
    out: list[dict[str, Any]] = []
    n = 0
    for surf in ordered:
        sid = str(surf.get("id") or f"surface{n}")
        path = str(surf.get("path") or "/")
        pw = str(surf.get("playwright") or f"e2e/{sid}.spec.ts")
        scenarios = surf.get("scenarios") or []
        if not scenarios:
            scenarios = [{"id": "smoke", "name": f"{sid} smoke", "steps": [f"Open {path}"]}]
        for sc in scenarios:
            if not isinstance(sc, dict):
                continue
            local = str(sc.get("id") or "step")
            name = str(sc.get("name") or local)
            steps = sc.get("steps") or []
            if not isinstance(steps, list):
                steps = [str(steps)]
            out.append(
                {
                    "global_id": f"S{n}",
                    "surface_id": sid,
                    "local_id": local,
                    "name": name,
                    "steps": [str(x) for x in steps],
                    "playwright": pw,
                    "path": path,
                    "title": str(surf.get("title") or sid),
                }
            )
            n += 1
    return out


def comet_doc_path(root: Path, cfg: dict[str, Any]) -> Path | None:
    if cfg.get("comet_doc"):
        p = root / str(cfg["comet_doc"])
        return p if p.is_file() else p  # may be missing
    for cand in DEFAULT_COMET_CANDIDATES:
        p = root / cand
        if p.is_file():
            return p
    docs = root / "docs"
    if docs.is_dir():
        for p in sorted(docs.glob("E2E*.md")):
            return p
    return root / DEFAULT_COMET


def find_playwright_config(root: Path, cfg: dict[str, Any]) -> Path | None:
    rel = cfg.get("playwright_config")
    if rel:
        p = root / str(rel)
        return p if p.is_file() else None
    for name in DEFAULT_PW_CONFIGS:
        p = root / name
        if p.is_file():
            return p
    return None


def find_e2e_specs(root: Path, cfg: dict[str, Any]) -> list[Path]:
    dirs: list[str] = []
    if cfg.get("e2e_dir"):
        dirs.append(str(cfg["e2e_dir"]))
    dirs.extend(DEFAULT_E2E_DIRS)
    seen: set[str] = set()
    out: list[Path] = []
    for d in dirs:
        if d in seen:
            continue
        seen.add(d)
        base = root / d
        if not base.is_dir():
            continue
        out.extend(base.glob("**/*spec.ts"))
        out.extend(base.glob("**/*.spec.ts"))
    # unique
    uniq: list[Path] = []
    seenp: set[Path] = set()
    for p in out:
        if p not in seenp:
            seenp.add(p)
            uniq.append(p)
    return uniq


def validate_web_e2e(root: Path) -> dict[str, Any]:
    det = detect_website(root)
    cfg = det["web_e2e"]
    result: dict[str, Any] = {
        "has_website": det["has_website"],
        "reasons": det["reasons"],
        "pass": True,
        "violations": [],
        "warnings": [],
        "scenarios": [],
        "comet_doc": None,
        "playwright_config": None,
    }
    if not det["has_website"]:
        result["skipped"] = True
        return result

    comet = comet_doc_path(root, cfg)
    assert comet is not None
    result["comet_doc"] = str(comet.relative_to(root)) if comet.is_file() else str(
        cfg.get("comet_doc") or DEFAULT_COMET
    )
    if not comet.is_file():
        result["pass"] = False
        result["violations"].append(f"missing Comet/E2E scenario doc: {result['comet_doc']}")
    else:
        text = comet.read_text(encoding="utf-8", errors="replace")
        low = text.lower()
        if not any(m.lower() in low for m in COMET_MARKERS_ANY):
            result["pass"] = False
            result["violations"].append(
                "scenario doc needs agent-readable steps "
                "(PROMPT FOR COMET / Report template / PASS|FAIL / scenarios)"
            )
        if "playwright" not in low and "e2e" not in low:
            result["warnings"].append("scenario doc should reference Playwright e2e files")

    pw = find_playwright_config(root, cfg)
    result["playwright_config"] = str(pw.relative_to(root)) if pw else None
    specs = find_e2e_specs(root, cfg)
    if not pw and not specs:
        result["pass"] = False
        result["violations"].append(
            "website detected but no playwright.config.* and no *spec.ts under e2e/ "
            "(or app/e2e/) — run scaffold_web_e2e.py"
        )

    surfaces = cfg.get("surfaces") if isinstance(cfg.get("surfaces"), list) else []
    if surfaces:
        allocated = allocate_scenario_ids(surfaces)
        result["scenarios"] = allocated
        for sc in allocated:
            p = root / sc["playwright"]
            if not p.is_file():
                result["pass"] = False
                result["violations"].append(f"missing Playwright file for {sc['global_id']}: {sc['playwright']}")
    else:
        result["warnings"].append(
            "web_e2e.surfaces not declared — IDs not allocated from plugin; add surfaces for deterministic S0..Sn"
        )

    # smoke recommendation
    plugin = load_plugin(root)
    smoke = plugin.get("smoke") if isinstance(plugin.get("smoke"), list) else []
    smoke_names = " ".join(str(s.get("name", "")) for s in smoke if isinstance(s, dict)).lower()
    smoke_cmds = " ".join(
        " ".join(str(x) for x in (s.get("cmd") or [])) for s in smoke if isinstance(s, dict)
    ).lower()
    if "e2e" not in smoke_names and "playwright" not in smoke_cmds and "test:e2e" not in smoke_cmds:
        result["warnings"].append(
            "smoke[] has no e2e/playwright step — add e.g. cmd: [npm, run, test:e2e] for web products"
        )

    return result


def machine_block(base_url: str, scenarios: list[dict[str, Any]], surfaces: list[dict[str, Any]]) -> str:
    lines = [
        "<!-- WEB_E2E_CONTRACT",
        "version: 1",
        f"base_url: {base_url}",
        "surfaces:",
    ]
    for s in sorted(surfaces, key=lambda x: (int(x.get("order", 1000)), str(x.get("id", "")))):
        lines.append(f"  - id: {s.get('id')}")
        lines.append(f"    path: {s.get('path', '/')}")
        lines.append(f"    playwright: {s.get('playwright', '')}")
    lines.append("scenarios:")
    for sc in scenarios:
        lines.append(f"  - {sc['global_id']}: {sc['surface_id']}/{sc['local_id']} — {sc['name']}")
    lines.append("-->")
    return "\n".join(lines)


def main_check_json(root: Path) -> int:
    r = validate_web_e2e(root)
    print(json.dumps(r, indent=2))
    return 0 if r.get("pass") else 1


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    root = args.root.resolve()
    r = validate_web_e2e(root)
    if args.json:
        print(json.dumps(r, indent=2))
    else:
        print(f"has_website={r['has_website']} reasons={r.get('reasons')}")
        for v in r.get("violations") or []:
            print(f"❌ {v}")
        for w in r.get("warnings") or []:
            print(f"⚠️  {w}")
        if r.get("scenarios"):
            print("scenarios:", ", ".join(s["global_id"] for s in r["scenarios"]))
        print("✅ web_e2e ok" if r.get("pass") else "❌ web_e2e failed")
    raise SystemExit(0 if r.get("pass") else 1)
