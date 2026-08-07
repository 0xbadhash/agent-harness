# Web E2E + Comet / Perplexity scenarios (default when a product has a website)

## Why

Products with a **browser surface** need two layers of QA:

1. **Playwright** — deterministic, CI-friendly, developer-owned  
2. **Comet / Perplexity scenarios** — human/agent browser QA against the **live** (or staged) URL  

Without a harness default, agents ship web UI and forget to update either layer.

## When this applies (auto-detect)

A product **has a website** if **any** of:

- `.agents/product_plugin.yaml` has `web_e2e.enabled: true`, **or**
- `web_e2e.auto_detect: true` (default when section present) and any of:
  - `web/` directory exists
  - root `index.html` / `app/web/` / `public/index.html`
  - `playwright.config.ts` / `.js` / `.mjs`
  - `e2e/**/*.spec.ts` already present
  - `docs/E2E_COMET_SCENARIOS.md` already present

Non-web products (CLI-only, libraries) skip the gate.

## Required artifacts (contract)

| Artifact | Path (default) | Role |
|----------|----------------|------|
| Comet scenario doc | `docs/E2E_COMET_SCENARIOS.md` | Human + Comet agent steps + report template |
| Playwright config | `playwright.config.ts` (or js/mjs) | Base URL, webServer |
| Specs | `e2e/*.spec.ts` | One file per surface (preferred) |
| Plugin block | `web_e2e:` in product_plugin | Surfaces, base_url, paths |

## Deterministic scenario IDs

**Never invent free-form scenario numbers.** Use this scheme:

```text
S0  = smoke / load (always first if surface has a page)
S1…Sn = functional scenarios for that surface, declared in order in product_plugin
```

**Global numbering** (Comet report): allocate contiguous IDs in **plugin surface order**:

1. Sort surfaces by explicit `order` (default: list order).  
2. For each surface, assign the next free `S{n}` for each scenario in `scenarios[]`.  
3. Write a machine block at the top of the Comet doc (see scaffold).

Re-running scaffold **recomputes** IDs from the plugin — do not hand-edit ID numbers without updating the plugin.

## Scaffold (source of truth generator)

```bash
# From product root (plugin must declare web_e2e.surfaces or allow auto-detect)
python3 scripts/scaffold_web_e2e.py --root . --write
# Dry-run
python3 scripts/scaffold_web_e2e.py --root . --print
```

Creates/updates:

- `docs/E2E_COMET_SCENARIOS.md` (PROMPT + tables + report)  
- Stub `e2e/<surface>.spec.ts` if missing  
- Stub `playwright.config.ts` if missing  

Does **not** overwrite existing Playwright tests unless `--force-tests`.

## Gates

```bash
python3 scripts/check_web_e2e.py --root .
# JSON for hard_gates / CI
python3 scripts/check_web_e2e.py --root . --json
```

**Fail closed** when a website **or browser app** is detected and **any** of:

| Requirement | Why |
|-------------|-----|
| Comet/E2E scenario doc | Agents (Comet/Perplexity) need human-readable S-ids |
| Playwright **config** | Deterministic local/CI runner |
| At least one `*spec.ts` | Automated regression |
| S-ids in `test("S0 …")` titles | Shared numbering with Comet |
| Every Playwright S-id appears in Comet doc | Same ship must update both |
| `web_e2e.surfaces` in product_plugin | Deterministic surface map |
| `smoke[]` includes e2e / `test:e2e` / playwright | Release smoke cannot skip browser |

**Opt out** only for non-UI products: `web_e2e.enabled: false`.

**Temporary migration** (not for ship): `web_e2e.strict: false` or `check_web_e2e.py --lenient` turns surfaces/smoke into warnings; S-id/Comet/Playwright artifacts still required when present.

Hard gates (`/pr_review --validate`) and `/release_mgmt` call this gate — a website product **cannot** score ≥95 or ship without it.

## Ship FSM duties (agents)

| Skill | Duty |
|-------|------|
| `/spec` | If acceptance includes UI, list scenario IDs to add/update |
| `/execute_dev` | Implement UI **and** update Playwright + Comet for those IDs |
| `/pr_review` | `check_web_e2e` via hard_gates when web surface in scope |
| `/release_mgmt` | Smoke includes unit + e2e when `web_e2e` enabled |
| `/sync_docs` | Keep Comet one-liner / raw GitHub URL current |

## product_plugin.yaml example

```yaml
web_e2e:
  enabled: true
  auto_detect: true
  base_url: https://example.com
  comet_doc: docs/E2E_COMET_SCENARIOS.md
  playwright_config: playwright.config.ts
  e2e_dir: e2e
  surfaces:
    - id: home
      order: 0
      path: /
      title: Home
      playwright: e2e/home.spec.ts
      scenarios:
        - id: smoke
          name: Smoke load
          steps:
            - "Open base_url + path"
            - "See primary heading"
    - id: about
      order: 1
      path: /about.html
      title: About
      playwright: e2e/about.spec.ts
      scenarios:
        - id: load
          name: About loads
          steps:
            - "Open about"
            - "See security copy"
```

## Comet one-liner pattern

> Read `https://raw.githubusercontent.com/<org>/<repo>/master/docs/E2E_COMET_SCENARIOS.md` and execute PROMPT FOR COMET (S0–Sn). Return the Report template.

## Anti-patterns

- Updating UI without Playwright  
- Hand-written Comet IDs that drift from plugin  
- Putting secrets in e2e or Comet docs  
- Using public explorer to brute-force seeds (product constitution)
