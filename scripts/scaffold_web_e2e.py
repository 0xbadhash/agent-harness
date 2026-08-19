#!/usr/bin/env python3
"""Scaffold / refresh Comet scenarios + Playwright stubs deterministically from product_plugin."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from product_plugin import load_plugin  # noqa: E402
from product_trait_contract import (  # noqa: E402
    ISO_RE,
    SECRET_WALL_RE,
    ensure_trait_scenarios,
    infer_traits,
)
from web_e2e_contract import (  # noqa: E402
    DEFAULT_E2E_DIR,
    allocate_scenario_ids,
    comet_doc_path,
    detect_website,
    machine_block,
)


def _default_surfaces(root: Path) -> list[dict]:
    """Filesystem fallback when plugin has no surfaces."""
    surfaces: list[dict] = []
    if (root / "web" / "index.html").is_file() or (root / "index.html").is_file():
        surfaces.append(
            {
                "id": "home",
                "order": 0,
                "path": "/",
                "title": "Home",
                "playwright": "e2e/home.spec.ts",
                "scenarios": [
                    {
                        "id": "smoke",
                        "name": "Smoke load",
                        "steps": ["Open /", "Page loads without console crash"],
                    }
                ],
            }
        )
    web = root / "web"
    if web.is_dir():
        order = 1
        for html in sorted(web.glob("*.html")):
            if html.name == "index.html":
                continue
            sid = html.stem.replace(".", "-")
            surfaces.append(
                {
                    "id": sid,
                    "order": order,
                    "path": f"/{html.name}",
                    "title": html.stem.title(),
                    "playwright": f"e2e/{sid}.spec.ts",
                    "scenarios": [
                        {
                            "id": "smoke",
                            "name": f"{html.stem} smoke",
                            "steps": [f"Open /{html.name}", "Primary heading visible"],
                        }
                    ],
                }
            )
            order += 1
    if not surfaces:
        surfaces.append(
            {
                "id": "app",
                "order": 0,
                "path": "/",
                "title": "App",
                "playwright": "e2e/app.spec.ts",
                "scenarios": [
                    {"id": "smoke", "name": "Smoke", "steps": ["Open base URL", "App shell visible"]}
                ],
            }
        )
    return surfaces


def render_comet(
    *,
    product_name: str,
    base_url: str,
    surfaces: list[dict],
    scenarios: list[dict],
    repo_hint: str,
) -> str:
    mb = machine_block(base_url, scenarios, surfaces)
    lines = [
        mb,
        "",
        f"# {product_name} — E2E suite for Comet / Perplexity",
        "",
        "**Canonical file:** `docs/E2E_COMET_SCENARIOS.md`",
        f"**Base URL:** {base_url}",
        "",
        "| Suite | Playwright | Scenarios |",
        "|-------|------------|-----------|",
    ]
    by_surf: dict[str, list[dict]] = {}
    for sc in scenarios:
        by_surf.setdefault(sc["surface_id"], []).append(sc)
    for sid, scs in by_surf.items():
        pw = scs[0]["playwright"]
        ids = ", ".join(s["global_id"] for s in scs)
        lines.append(f"| {sid} | `{pw}` | {ids} |")

    lines += [
        "",
        "Run: `npm run test:e2e` (or product equivalent) · live: set `BASE_URL=`",
        "",
        "---",
        "",
        "## PROMPT FOR COMET / PERPLEXITY",
        "",
        "```text",
        f"You are a browser QA agent for {product_name}.",
        f"SOURCE OF TRUTH: docs/E2E_COMET_SCENARIOS.md ({repo_hint}).",
        f"BASE_URL: {base_url}",
        "Hard-refresh once per surface, then execute every scenario S0…Sn in order.",
        "Mark PASS/FAIL with one line of evidence. Final output MUST use the Report template.",
        "Never use real secrets / funded seeds unless the product explicitly provides a public test vector.",
        "```",
        "",
        "---",
        "",
        "## Scenarios (deterministic IDs from product_plugin web_e2e.surfaces)",
        "",
    ]
    for sc in scenarios:
        lines.append(f"### {sc['global_id']} — {sc['name']} (`{sc['surface_id']}/{sc['local_id']}`)")
        lines.append("")
        lines.append(f"**URL:** `{base_url.rstrip('/')}{sc['path']}`  ")
        lines.append(f"**Playwright:** `{sc['playwright']}`")
        lines.append("")
        lines.append("| Step | Action / expected |")
        lines.append("|------|-------------------|")
        for i, step in enumerate(sc["steps"] or ["Complete scenario"], 1):
            lines.append(f"| {i} | {step} |")
        lines.append("")

    lines += [
        "---",
        "",
        "## Report template",
        "",
        "```text",
        f"# {product_name} E2E report",
        f"Base URL: {base_url}",
        "Date (UTC):",
        "Agent: Comet / Perplexity / other:",
        "",
    ]
    for sc in scenarios:
        lines.append(f"{sc['global_id']} {sc['name']}: PASS|FAIL — ")
    score_n = len(scenarios)
    lines += [
        "",
        f"Score: __ / {score_n} PASS",
        "Blockers:",
        "Notes:",
        "```",
        "",
        "---",
        "",
        "## Operator one-liner for Comet",
        "",
        f"> Read the raw `docs/E2E_COMET_SCENARIOS.md` for this repo and execute PROMPT FOR COMET "
        f"(S0–S{max(0, score_n - 1)}) against {base_url}. Return the Report template.",
        "",
        "## Playwright (developers)",
        "",
        "```bash",
        "npm install && npx playwright install chromium",
        "npm run test:e2e",
        "```",
        "",
        "Regenerate this file (IDs + tables) after editing `web_e2e.surfaces` in product_plugin:",
        "",
        "```bash",
        "python3 scripts/scaffold_web_e2e.py --root . --write",
        "```",
        "",
    ]
    return "\n".join(lines)


def _named_stub_body(sc: dict) -> str:
    """Named stub — contract comment + skip, not a tautological body-visible assert."""
    gid = sc["global_id"]
    name = sc["name"]
    path = sc["path"]
    local = sc["local_id"]
    blob = f"{local} {name}"
    if ISO_RE.search(blob):
        contract = (
            "CONTRACT: holder A never painted as holder B; "
            "garbage / wrong id → plain English error, not another person (IDOR)."
        )
        skip_reason = "scaffold named stub: implement isolation assertions"
    elif SECRET_WALL_RE.search(blob):
        contract = (
            "CONTRACT: no mnemonic/seed export; no sessionStorage/localStorage leak "
            "of client secrets."
        )
        skip_reason = "scaffold named stub: implement secret-wall assertions"
    else:
        contract = f"CONTRACT: implement real assertions for {gid} — not body-visible tautology."
        skip_reason = f"scaffold named stub: implement {gid} assertions"

    steps = sc.get("steps") or []
    steps_c = "\n".join(f"   * - {s}" for s in steps) or "   * - (add steps)"
    return f'''  /**
   * {contract}
{steps_c}
   */
  test.skip("{gid} {name}", async ({{ page }}) => {{
    await page.goto("{path}");
    // {skip_reason}
    void page;
  }});
'''


def render_spec_ts(surface_id: str, path: str, title: str, scenarios: list[dict] | None = None) -> str:
    """Emit named S-id stubs (test.skip with S-id in title) — never tautological smoke-only."""
    scenarios = scenarios or []
    if not scenarios:
        # Fallback single named smoke stub (still S-id shaped when allocated elsewhere)
        scenarios = [
            {
                "global_id": "S0",
                "local_id": "smoke",
                "name": f"{title} smoke — replace with real assertion",
                "path": path,
                "steps": [f"Open {path}", "Assert primary control (not merely body visible)"],
            }
        ]
    bodies = "\n".join(_named_stub_body(sc) for sc in scenarios)
    return f'''import {{ test, expect }} from "@playwright/test";

/** Auto-scaffolded surface: {surface_id} — named stubs (not tautological). */
test.describe("{surface_id}", () => {{
{bodies}}});
'''


def render_pw_config(base_url: str, web_dir: str | None) -> str:
    web_server = ""
    if web_dir:
        web_server = f'''
  webServer: process.env.BASE_URL
    ? undefined
    : {{
        command: "python3 -m http.server 4173 --directory {web_dir}",
        url: "http://127.0.0.1:4173",
        reuseExistingServer: !process.env.CI,
        timeout: 30_000,
      }},'''
    return f'''import {{ defineConfig, devices }} from "@playwright/test";

const baseURL = process.env.BASE_URL || "http://127.0.0.1:4173";

export default defineConfig({{
  testDir: "./e2e",
  fullyParallel: false,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  reporter: [["list"]],
  timeout: 60_000,
  use: {{
    baseURL,
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  }},
  projects: [{{ name: "chromium", use: {{ ...devices["Desktop Chrome"] }} }}],{web_server}
}});
'''


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--write", action="store_true", help="Write files")
    ap.add_argument("--print", dest="do_print", action="store_true", help="Print Comet doc to stdout")
    ap.add_argument("--force-tests", action="store_true", help="Overwrite existing e2e stubs")
    ap.add_argument("--force-comet", action="store_true", help="Overwrite Comet doc entirely")
    args = ap.parse_args()
    root = args.root.resolve()
    plugin = load_plugin(root)
    det = detect_website(root, plugin)
    cfg = det["web_e2e"] if isinstance(det.get("web_e2e"), dict) else {}

    if not det["has_website"] and not cfg.get("surfaces"):
        print("No website detected and no web_e2e.surfaces — nothing to scaffold.", file=sys.stderr)
        return 1

    surfaces = cfg.get("surfaces") if isinstance(cfg.get("surfaces"), list) else None
    if not surfaces:
        surfaces = _default_surfaces(root)
        print("⚠️  No web_e2e.surfaces in plugin — using filesystem defaults (add surfaces for stable IDs)")

    traits = infer_traits(root, plugin)
    surfaces = ensure_trait_scenarios(surfaces, traits)
    if traits.get("web3", {}).get("active"):
        print("· web3 trait — ensuring isolation (iso-two-holder) named scenario")
    if traits.get("client_secrets", {}).get("active"):
        print("· client_secrets trait — ensuring secret-wall named scenario")

    scenarios = allocate_scenario_ids(surfaces)
    _raw_ns = plugin.get("night_shift")
    ns: dict[str, Any] = _raw_ns if isinstance(_raw_ns, dict) else {}
    base_url = str(cfg.get("base_url") or ns.get("default_host") or "http://127.0.0.1:4173")
    if base_url and not str(base_url).startswith("http"):
        base_url = "https://" + base_url
    product_name = str(plugin.get("product_name") or plugin.get("product_id") or root.name)
    repo_hint = str(plugin.get("product_id") or root.name)

    doc = render_comet(
        product_name=product_name,
        base_url=base_url,
        surfaces=surfaces,
        scenarios=scenarios,
        repo_hint=repo_hint,
    )

    if args.do_print or not args.write:
        print(doc)
        if not args.write:
            print("\n# dry-run: pass --write to create files", file=sys.stderr)

    if args.write:
        comet = comet_doc_path(root, cfg)
        comet.parent.mkdir(parents=True, exist_ok=True)
        if comet.is_file() and not args.force_comet:
            # Merge strategy: if machine block missing, prepend; else rewrite full when force
            existing = comet.read_text(encoding="utf-8")
            if "WEB_E2E_CONTRACT" not in existing:
                comet.write_text(machine_block(base_url, scenarios, surfaces) + "\n\n" + existing, encoding="utf-8")
                print(f"  ~ prepended WEB_E2E_CONTRACT → {comet.relative_to(root)}")
            else:
                print(f"  = left existing Comet doc (use --force-comet to regenerate): {comet.relative_to(root)}")
        else:
            comet.write_text(doc, encoding="utf-8")
            print(f"  + {comet.relative_to(root)}")

        e2e_dir = root / str(cfg.get("e2e_dir") or DEFAULT_E2E_DIR)
        e2e_dir.mkdir(parents=True, exist_ok=True)
        by_pw: dict[str, list[dict]] = {}
        for sc in scenarios:
            by_pw.setdefault(sc["playwright"], []).append(sc)
        for rel, scs in by_pw.items():
            path = root / rel
            if path.is_file() and not args.force_tests:
                print(f"  = keep {rel}")
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            head = scs[0]
            path.write_text(
                render_spec_ts(
                    head["surface_id"],
                    head["path"],
                    head.get("title") or head["surface_id"],
                    scenarios=scs,
                ),
                encoding="utf-8",
            )
            print(f"  + {rel} ({', '.join(s['global_id'] for s in scs)})")

        pw_name = str(cfg.get("playwright_config") or "playwright.config.ts")
        pw_path = root / pw_name
        if not pw_path.is_file():
            web_dir = "web" if (root / "web").is_dir() else None
            pw_path.write_text(render_pw_config(base_url, web_dir), encoding="utf-8")
            print(f"  + {pw_name}")
        else:
            print(f"  = keep {pw_name}")

        print("IDs:", " ".join(s["global_id"] for s in scenarios))
        print("Next: declare web_e2e.surfaces in product_plugin.yaml; add smoke e2e; implement assertions.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
