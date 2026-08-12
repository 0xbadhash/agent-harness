# CI matrix: jobs × repos × fail-closed

**SoT:** agent-harness (see `VERSION`)  
**Principle:** merge bar = disk + tests + hard_gates; continuous security is extra jobs, not a second product.

## Job catalog

| Job ID | Harness mapping | Fail-closed? | When |
|--------|-----------------|--------------|------|
| **J1 unit** | pytest / product tests | **Yes** | every PR + main |
| **J2 lint/type** | ruff + mypy (when configured) | **Yes** | every PR + main |
| **J3 hardcodes** | `check_hardcodes.py` | **Yes** | every PR + main |
| **J4 validate** | `validate.py full` | **Yes** | every PR + main |
| **J5 daytime subset** | `daytime_readiness_subset.py` | **Yes** | PR/main + VPS |
| **J6 hard_gates** | `pr_validator` / `hard_gates` | **Yes** (skip only with `ALLOW_SKIP_HARD_GATES=1` + log) | ship PR |
| **J7 secrets** | `check_secrets_diff.py` | **Yes** | every code PR |
| **J8 skill-conformance** | `agent_eval_checklist` | **Yes when run** | harness path-filter |
| **J9 web e2e** | `check_web_e2e` / Playwright | **Yes** if website | UI / website products |
| **J10 product_smoke** | plugin `smoke[]` | **Yes** | daytime + release |
| **J11 dep audit** | `check_lockfile_audit` | **Yes** if tool present | lockfile diff |
| **J12 Semgrep** | `.semgrep.yml` + CI job | **Yes** (error severity) | every PR |
| **J13 ZAP baseline** | `scripts/zap_baseline.sh` + workflow | **Warn** then optional strict | schedule / staging hosts |
| **J14 property tests** | plugin `property_tests:` + pytest | **Yes** as unit tests | modules listed in plugin |
| **J15 night_shift** | VPS timer | **Yes** (ops) | schedule |
| **J16 protect SoT pin** | `check_protect_sot_pin` | **Warn** | portfolio report |

## Repo × job matrix

**F** = fail-closed · **W** = warn · **—** = N/A · **S** = selective

| Job | harness | watchlist | email-detach | substack | second-brain | catalyxt | ocr | zk | bip39 |
|-----|:-------:|:---------:|:------------:|:--------:|:------------:|:--------:|:---:|:--:|:-----:|
| J1–J5, J7 | F | F | F | F | F | F | F | F | F |
| J6 ship | F | F | F | F | F | F | F | F | F |
| J8 skills | F/S | — | — | — | — | — | — | — | — |
| J9 web e2e | — | F | — | — | — | F | — | S | F |
| J10 smoke | S | F | F | F | F | F | F | F | F |
| J11 audit | S | S | S | S | S | S | S | S | S |
| J12 Semgrep | F | F | F | F | F | F | F | F | F |
| J13 ZAP | — | W host | — | — | — | W host | — | — | W host |
| J14 property | S | S | S | — | — | — | S | S | S |
| J15 night | F | F | F | F | F | F | F | F | F |
| J16 pin | SoT | W | W | W | W | W | W | W | W |

## Ship chain mapping

```
PR / main push
  J1 unit · J2 lint · J3 hardcodes · J4 validate · J5 daytime · J7 secrets · J12 Semgrep
  J9 web e2e (website) · J11 lockfile (if changed)

Ship closeout (/pr_review --validate)
  J6 hard_gates  → score ≥ 95
  --skip-hard-gates requires ALLOW_SKIP_HARD_GATES=1 (logged)

Release
  J10 smoke (+ J9 if website)

Schedule
  J15 night_shift · J13 ZAP staging (config/zap_targets.yaml)
```

## Adoption steps (implemented)

| Step | Deliverable |
|------|-------------|
| 1 | Product `templates/daytime-gates.yml` fail-closed J1–J5+J7; install copies to `.github/workflows/` |
| 2 | `pr_validator --skip-hard-gates` requires `ALLOW_SKIP_HARD_GATES=1`; always logs skip |
| 3 | `.semgrep.yml` + Semgrep job in harness + product daytime template |
| 4 | `scripts/zap_baseline.sh` + `config/zap_targets.yaml` + `templates/zap-baseline.yml` |
| 5 | `property_tests` in product_plugin + `check_property_tests.py` + hard_gates hook |

## Illegal

- ZAP/OSS-Fuzz as substitute for J6  
- Semgrep as substitute for AC map  
- Silent `--skip-hard-gates` without env + log  
