#!/usr/bin/env python3
"""Web E2E + Comet scenario contract: detect website/app UI, validate artifacts, allocate S-ids.

When a product has a website or browser app, Playwright + Comet/Perplexity scenarios
and an e2e smoke step are **mandatory** (fail closed). Opt out only with
``web_e2e.enabled: false`` in product_plugin.yaml.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from product_plugin import load_plugin

# Playwright test("S12 …") or test('S0b …')
_PLAYWRIGHT_TEST_TITLE = re.compile(
    r"""(?m)test\s*(?:\.only|\.skip)?\s*\(\s*(['"`])(.*?)\1""",
    re.DOTALL,
)
_SCENARIO_ID = re.compile(r"\bS\d+[a-z]?\b")

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


def _detect_package_web_app(root: Path) -> list[str]:
    """Signals of a browser app (SPA/SSR) even without a web/ folder."""
    reasons: list[str] = []
    pkg = root / "package.json"
    if not pkg.is_file():
        return reasons
    try:
        data = json.loads(pkg.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return reasons
    scripts = data.get("scripts") if isinstance(data.get("scripts"), dict) else {}
    deps: dict[str, Any] = {}
    for key in ("dependencies", "devDependencies", "peerDependencies"):
        block = data.get(key)
        if isinstance(block, dict):
            deps.update(block)
    joined = " ".join(str(k).lower() for k in deps)
    if any(
        k in joined
        for k in (
            "next",
            "react-dom",
            "vue",
            "@angular/core",
            "svelte",
            "vite",
            "nuxt",
            "@remix-run",
            "astro",
        )
    ):
        reasons.append("package.json browser framework")
    if any("test:e2e" in str(v) or "playwright" in str(v).lower() for v in scripts.values()):
        reasons.append("package.json e2e script")
    if "playwright" in joined or "@playwright/test" in joined:
        reasons.append("package.json @playwright/test")
    return reasons


def detect_website(root: Path, plugin: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return {has_website, reasons[], web_e2e config}.

    True for static sites **or** browser apps. Opt out with ``web_e2e.enabled: false``.
    """
    plugin = plugin if plugin is not None else load_plugin(root)
    cfg = _as_dict(plugin.get("web_e2e"))

    if cfg.get("enabled") is True:
        return {"has_website": True, "reasons": ["web_e2e.enabled=true"], "web_e2e": cfg}
    if cfg.get("enabled") is False:
        return {"has_website": False, "reasons": ["web_e2e.enabled=false"], "web_e2e": cfg}

    # enabled unset → auto-detect filesystem (and honor explicit surfaces/base_url)
    reasons: list[str] = []
    if (root / "web").is_dir():
        reasons.append("web/")
    if (root / "index.html").is_file():
        reasons.append("index.html")
    if (root / "public" / "index.html").is_file():
        reasons.append("public/index.html")
    if (root / "app" / "web").is_dir():
        reasons.append("app/web/")
    if (root / "app" / "page.tsx").is_file() or (root / "app" / "page.jsx").is_file():
        reasons.append("app/page (Next-style)")
    if (root / "src" / "App.tsx").is_file() or (root / "src" / "App.jsx").is_file():
        reasons.append("src/App (SPA)")
    if any((root / name).is_file() for name in DEFAULT_PW_CONFIGS):
        reasons.append("playwright.config")
    for ed in DEFAULT_E2E_DIRS:
        e2e = root / ed
        if e2e.is_dir() and (
            list(e2e.glob("**/*spec.ts")) or list(e2e.glob("**/*.spec.ts"))
        ):
            reasons.append(f"{ed}/*.spec.ts")
            break
    for cand in DEFAULT_COMET_CANDIDATES:
        if (root / cand).is_file():
            reasons.append(cand)
            break
    docs = root / "docs"
    if (
        docs.is_dir()
        and (
            list(docs.glob("*COMET*"))
            or list(docs.glob("*E2E*SCENARIO*"))
            or list(docs.glob("E2E*.md"))
        )
        and not any(str(r).startswith("docs/") for r in reasons)
    ):
        reasons.append("docs/E2E*")

    reasons.extend(_detect_package_web_app(root))

    if cfg.get("surfaces") or cfg.get("base_url"):
        reasons.append("web_e2e.surfaces|base_url")

    auto = cfg.get("auto_detect", True)
    has = bool(reasons) if auto else bool(cfg.get("surfaces") or cfg.get("base_url"))
    return {"has_website": has, "reasons": reasons, "web_e2e": cfg}


def extract_playwright_scenario_ids(specs: list[Path]) -> set[str]:
    """Collect S-ids from Playwright test() titles (e.g. S0, S18b)."""
    found: set[str] = set()
    for path in specs:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for m in _PLAYWRIGHT_TEST_TITLE.finditer(text):
            title = m.group(2).split("\n")[0]
            for sid in _SCENARIO_ID.findall(title):
                found.add(sid)
    return found


def extract_comet_scenario_ids(text: str) -> set[str]:
    """S-ids appearing in Comet/scenario doc (headings, report template, prose)."""
    return set(_SCENARIO_ID.findall(text or ""))


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


def comet_doc_path(root: Path, cfg: dict[str, Any]) -> Path:
    if cfg.get("comet_doc"):
        return root / str(cfg["comet_doc"])  # may be missing
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


def validate_web_e2e(root: Path, *, strict: bool | None = None) -> dict[str, Any]:
    """Validate mandatory web/app E2E contract.

    When ``has_website`` is true, fail closed unless Playwright, Comet doc,
    plugin surfaces, and smoke e2e are present. Set ``web_e2e.strict: false``
    in the product plugin only for temporary migration (not recommended).

    ``strict`` argument overrides plugin ``web_e2e.strict`` (default True).
    """
    det = detect_website(root)
    cfg = det["web_e2e"]
    if strict is None:
        strict = cfg.get("strict", True) is not False
    result: dict[str, Any] = {
        "has_website": det["has_website"],
        "reasons": det["reasons"],
        "pass": True,
        "violations": [],
        "warnings": [],
        "scenarios": [],
        "playwright_s_ids": [],
        "comet_s_ids": [],
        "missing_in_comet": [],
        "comet_doc": None,
        "playwright_config": None,
        "strict": strict,
    }
    if not det["has_website"]:
        result["skipped"] = True
        return result

    comet = comet_doc_path(root, cfg)
    result["comet_doc"] = str(comet.relative_to(root)) if comet.is_file() else str(
        cfg.get("comet_doc") or DEFAULT_COMET
    )
    comet_text = ""
    if not comet.is_file():
        result["pass"] = False
        result["violations"].append(
            f"missing Comet/E2E scenario doc: {result['comet_doc']} "
            "(required for website/app products — scaffold_web_e2e.py or write docs/E2E_COMET_SCENARIOS.md)"
        )
    else:
        comet_text = comet.read_text(encoding="utf-8", errors="replace")
        low = comet_text.lower()
        if not any(m.lower() in low for m in COMET_MARKERS_ANY):
            result["pass"] = False
            result["violations"].append(
                "scenario doc needs agent-readable steps "
                "(PROMPT FOR COMET / Report template / PASS|FAIL / scenarios)"
            )
        if "playwright" not in low and "e2e" not in low:
            result["pass"] = False
            result["violations"].append(
                "scenario doc must reference Playwright e2e files (so agents keep both in sync)"
            )
        result["comet_s_ids"] = sorted(extract_comet_scenario_ids(comet_text))

    pw = find_playwright_config(root, cfg)
    result["playwright_config"] = str(pw.relative_to(root)) if pw else None
    specs = find_e2e_specs(root, cfg)
    result["e2e_spec_count"] = len(specs)

    # Mandatory: both config and at least one spec (not either-or)
    if not pw:
        result["pass"] = False
        result["violations"].append(
            "website/app detected but no playwright.config.* — add Playwright config "
            "(see docs/web-e2e-comet.md)"
        )
    if not specs:
        result["pass"] = False
        result["violations"].append(
            "website/app detected but no *spec.ts under e2e/ (or app/e2e/) — "
            "add Playwright tests; run scaffold_web_e2e.py"
        )

    pw_ids = extract_playwright_scenario_ids(specs) if specs else set()
    result["playwright_s_ids"] = sorted(pw_ids)
    if specs and not pw_ids and cfg.get("require_s_ids", True) is not False:
        result["pass"] = False
        result["violations"].append(
            "Playwright specs found but no S-ids in test() titles "
            "(name tests like test('S0 smoke …') for Comet alignment; "
            "or set web_e2e.require_s_ids: false during migration)"
        )
    if pw_ids and comet_text:
        comet_ids = set(result["comet_s_ids"])
        missing = sorted(pw_ids - comet_ids)
        result["missing_in_comet"] = missing
        if missing:
            result["pass"] = False
            result["violations"].append(
                "Playwright S-ids missing from Comet/scenario doc (update both in the same ship): "
                + ", ".join(missing[:24])
                + ("…" if len(missing) > 24 else "")
            )

    surfaces = cfg.get("surfaces") if isinstance(cfg.get("surfaces"), list) else []
    if surfaces:
        allocated = allocate_scenario_ids(surfaces)
        result["scenarios"] = allocated
        for sc in allocated:
            p = root / sc["playwright"]
            if not p.is_file():
                result["pass"] = False
                result["violations"].append(
                    f"missing Playwright file for {sc['global_id']}: {sc['playwright']}"
                )
    else:
        msg = (
            "web_e2e.surfaces not declared — required for website/app products "
            "(deterministic S0…Sn); see product_plugin.example.yaml and docs/web-e2e-comet.md"
        )
        if strict:
            result["pass"] = False
            result["violations"].append(msg)
        else:
            result["warnings"].append(msg)

    # smoke[] e2e step is mandatory for website/app products
    plugin = load_plugin(root)
    _raw_smoke = plugin.get("smoke")
    smoke: list[Any] = _raw_smoke if isinstance(_raw_smoke, list) else []
    smoke_names = " ".join(str(s.get("name", "")) for s in smoke if isinstance(s, dict)).lower()
    smoke_cmds = " ".join(
        " ".join(str(x) for x in (s.get("cmd") or [])) for s in smoke if isinstance(s, dict)
    ).lower()
    has_e2e_smoke = (
        "e2e" in smoke_names
        or "playwright" in smoke_cmds
        or "test:e2e" in smoke_cmds
        or "playwright test" in smoke_cmds
    )
    if not has_e2e_smoke:
        msg = (
            "smoke[] has no e2e/playwright step — website/app products must include e.g. "
            "cmd: [npm, run, test:e2e] in product_plugin.yaml smoke (mandatory for release)"
        )
        if strict:
            result["pass"] = False
            result["violations"].append(msg)
        else:
            result["warnings"].append(msg)

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
