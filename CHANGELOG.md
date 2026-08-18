# Changelog

## v1.4.32 — 2026-08-18

### surface_inventory pane call

- `scripts/surface_inventory.py` lists known Catalyxt hosts by default (exit 0)
- No env flag required for list; no domain-find; CEO host list only
- Unit: `tests/test_surface_inventory.py`

## v1.4.31 — 2026-08-18

### Night parallel + Waiting leftovers

- `bin/night_shift_all_products.py --jobs` parallel products (default min(n,10)); wall/cpu timing
- `scripts/surface_inventory.py` optional declared-surface inventory (no domain-find)
- ship_skills vs next_skill: `/plan_review` after Spec+Plan; qa_campaign/retrospect/audit_harness → optional
- Archive leftover `*-plan.md`; skills/plan_review SoT
- pipeline/SESSION_CONTEXT refreshed; night reports link schedule SoT once
- `zap_summarize.py` → SUMMARY.md (raw HTML not in loops); ZAP not in night_all

## v1.4.30 — 2026-08-15

### Outer loop (plan / tickets / plan-review)

- **Plan fail-closed** for large non-waiver ships (`check_outer_loop.py` → hard_gates)
- **Tickets** required when plan Implementation sequence ≥ N (default 4)
- **Pre-code** `/plan_review` → PLAN_REVIEW.md when plan required
- **Playbook:** `docs/outer-loop-playbook.md` (host design/stack + P0 grill)
- P0 grill: operator stays on G1–G3 (process, no extra heavy gate)

## v1.4.29 — 2026-08-15

### Skills portfolio slim

- **Removed:** `feedback`, `plan_backend`, `audit_repo`, `test_automation` (see `removed_portable_skills.txt`)
- **Demoted (optional):** `agent_transcript`, `session_viewer` → `optional_skills.txt`
- **Merged:** plan_backend → `/spec --roadmap-from-gap`; test_automation → `/night_shift` suites; audit_repo narrative → `/audit_harness`
- **Primary hygiene obsolete-scan:** `/sweep`
- ship_skills required set: 14 skills

## v1.4.28 — 2026-08-12

### Tier A/B/C Best-of-Agent-Harnesses

- **A1** `harness.manifest.yaml` + `check_harness_manifest.py`
- **A2** `docs/compatibility.md` + `check_compatibility.py`
- **A3** `protect_sot_merge.py` + `config/critical_sot_scripts.txt`
- **A4** `SCANNER_STRICT` in secrets + lockfile audit; `docs/scanner-policy.md`
- **B1** MCP contract doc + `check_mcp_contract.py`
- **B2** recovery demo + `docs/recovery-demo.md`
- **B3** `evidence_hash.py`
- **B4** prompt-injection fixtures + `check_pi_fixtures.py`
- **B5** `github_daytime_status.py` + OPS embed
- **C1–C5** benchmark, SBOM/signing, sandbox policy, opt-in telemetry
- **C15** multi-agent runtime documented **NON_GOAL**
- Tests: `tests/test_tier_abc_1_4_28.py`

## v1.4.27 — 2026-08-12

### Ops: when tests run
- `scripts/test_trigger_schedule.py` — SoT schedule (ship / CI / night / ZAP / IoC)
- OPS-DASHBOARD embeds full act map every refresh
- Product `night-shift-log.md` embeds compact schedule
- Night readiness reports: schedule + gate **When else** column
- `docs/test-trigger-schedule.md`

## v1.4.26 — 2026-08-12

### CI matrix adoption (steps 1–5)
1. Product + harness **daytime-gates** fail-closed J1–J5+J7; install copies workflow
2. **J6** `--skip-hard-gates` requires `ALLOW_SKIP_HARD_GATES=1` + skip log
3. **J12 Semgrep** `.semgrep.yml` + CI job
4. **J13 ZAP** `zap_baseline.sh` + `config/zap_targets.yaml` (catalyxt/watchlist/bip39)
5. **J14 property_tests** plugin field + `check_property_tests` in hard_gates
- `docs/ci-matrix.md` one-page matrix

## v1.4.25 — 2026-08-10

### HSQ-3 P3 protect SoT pin (warn)
- **G15** `check_protect_sot_pin.py` — warn when pipeline_state/hard_gates diverge from SoT
- portfolio_install_report notes SoT pin drift
- mypy fix for check_security_paths

## v1.4.24 — 2026-08-10

### HSQ-3 P2 quality gates
- **G2** `check_spec_hash.py` — Spec path exists; optional spec_sha256 pin
- **G10** `check_waiver_budget.py` — rolling waiver budget on waiver ships
- **G7** `check_threat_tags.py` — runtime Threat notes ≥2 known tags
- **G8** `check_security_paths.py` — plugin security_paths → security tests

## v1.4.23 — 2026-08-10

### HSQ-3 P1 quality gates
- **G3** `check_changed_path_tests.py` — changed src needs test ref or ## Untested paths
- **G4** `check_red_green_cmds.py` — execute red_cmd/green_cmd from PR_DRAFT
- **G6** `check_lockfile_audit.py` — npm audit / pip-audit when lockfiles change
- hard_gates wires G3/G4/G6

## v1.4.22 — 2026-08-10

### HSQ-3 P0 quality gates
- **G1** `check_ac_traceability.py` — AC-n in spec → Traceability + tests (or N/A)
- **G5** expanded `check_secrets_diff` patterns (JWT, sk-, npm_, AIza, stripe, bearer)
- **G14** `check_diff_compile.py` — py_compile changed `.py` on ship diff
- hard_gates wires G1 + G14 for non-prose ships

## v1.4.21 — 2026-08-10

### HSQ-2 Integrity & Ops (items 1–9)
1. FSM `ALLOWED_TRANSITIONS` + `--force-transition` log
2. `run_ship_chain --allow-auto-markers` (default off)
3. Real CI skill-conformance path filter
4. Vault `/opt` defaults demoted to last-resort warn
5. `docs/protect-list-merge.md` playbook
6. OPS-DASHBOARD 30d waiver summary
7. `OPS_SNAPSHOTS.jsonl` daily append
8. CODE-REVIEW quality floor (min chars + verdict; auto-stubs fail)
9. `SKIP_HARD_GATES_LOG.jsonl` on `--skip-hard-gates`

## v1.4.20 — 2026-08-10

### HSQ-1 Ship Quality SoT
- **PR1:** `review_scope` thresholds configurable via `product_plugin.yaml` `review_scope:`
- **PR2:** Spec waiver append-only log `WAIVER_LOG.jsonl` + `waiver_report.py`
- **PR3:** Daytime CI documents skill conformance as `agent_eval_checklist` job
- **PR4:** `portfolio_install_report.py --force` and `--protect-drift`
- **PR5:** Ship-flow docs for Security IOC (ops, not PR hard gate)

## v1.4.19 — 2026-08-07

### Added
- **OPS weekly deep IoC scan:** `scripts/security_root_ioc_scan.py` + `deploy/security-root-ioc.{service,timer}`
  (Sun 04:30 UTC, root + `/opt` + containerd). Writes `agent-tasks/security-ioc-status.md`;
  findings refresh OPS-DASHBOARD fail rows; clean → green line only.
- `ops_dashboard` reads weekly IoC JSON; prefers morning triage recheck for night status.

### Fixed
- Night readiness reds on agent-harness / catalyxt / substack-push / watchlist (type/lint, hardcode
  newsjack allowlist, e2e `test:e2e` + Playwright webServer, coverage baseline).

v1.4.18 — 2026-08-07

### Changed — **mandatory** web/app E2E (fail closed)
- `validate_web_e2e` now **requires** for any detected website or browser app:
  - Playwright config **and** ≥1 `*spec.ts`
  - Comet/E2E scenario doc with agent markers + Playwright reference
  - S-ids in Playwright `test("S0 …")` titles
  - **Every** Playwright S-id listed in the Comet doc (same-ship sync)
  - `web_e2e.surfaces` in product_plugin
  - `smoke[]` step with e2e / `test:e2e` / playwright
- Detects SPA/SSR apps via `package.json` (react-dom, next, vite, …) and `app/page` / `src/App`
- Opt out: `web_e2e.enabled: false` · migration: `web_e2e.strict: false` or `check_web_e2e.py --lenient`
- Docs + example plugin + tests updated

### Why
Agents updated UI without systematically updating Playwright **and** Comet; soft warnings were ignored at score time.

## v1.4.17 — 2026-08-07

### Added
- **Web E2E + Comet default** for products with a website:
  - `docs/web-e2e-comet.md` — contract, deterministic S0…Sn IDs
  - `scripts/web_e2e_contract.py` — detect website, allocate IDs, validate
  - `scripts/check_web_e2e.py` — gate (bootstrap + hard_gates + release)
  - `scripts/scaffold_web_e2e.py` — regenerate Comet doc + Playwright stubs from `web_e2e.surfaces`
- `product_plugin.example.yaml` → `web_e2e:` block
- `hard_gates` / `execute_dev` / `release_mgmt` / `AGENTS.harness.md` require Playwright + Comet updates on UI ships
- Tests: `tests/test_web_e2e_contract.py`

### Why
Agents were shipping web UI without updating Playwright or Comet/Perplexity scenarios. Website products now fail closed until both exist and stay in the FSM.

## v1.4.16 — 2026-08-06

### Added
- **`scripts/ops_dashboard.py`** — single Obsidian front door (`agent-tasks/OPS-DASHBOARD.md`): what went well / failing / todos with wikilinks
- Aggregates night_shift, catalyxt news, vault health, kanban, portfolio lag, npm keyv seed security recheck
- **`deploy/ops-dashboard.{service,timer}`** — refresh 01:00 + 12:00 UTC

## v1.4.15 — 2026-08-03

### Docs / CODER overlay (P2–P3)
- **CODER mode labels** on ship-flow-detailed + skills-catalog (C/O/D/E/R teaching overlay)
- **`scripts/session_context.py`** — one-shot Organize pack → SESSION_CONTEXT.md
- **`docs/prompt-patterns.md`** — Jules White–style prompt patterns → harness skills
- Install copies `prompt-patterns.md`; llm-bootstrap session-start pointer

## v1.4.14 — 2026-08-03

### Docs
- **`docs/ship-flow-detailed.md`** — detailed harness flow for operators + LLMs (phases, NEXT_SKILL, TDD, hard/soft gates, skills, scripts)
- **Mermaid** diagrams embedded; **Draw.io + SVG** poster under `docs/diagrams/ship-flow-overview.{drawio,svg}`
- Links from ship-flow, llm-bootstrap, skills-catalog, README; install copies detailed flow + diagrams into products

## v1.4.13 — 2026-08-02

### Added
- **P0 A1** `scripts/run_ship_chain.py` — deterministic unattended score→ship→push (no LLM)
- **P0 A5/A8** `scripts/night_fail_remediate.py` — bounded autofix + recheck + NIGHT_FAIL_TICKETS
- **A4 default** release_mgmt: post-tag `portfolio_install_report.py --install --push`
- Morning timer runs triage then remediate

## v1.4.12 — 2026-08-02

### Added (P0–P1 feedback loops)
- **A1/A3** `scripts/finish_ship.py` → PUSH_PROOF.md (+ `--require-push`)
- **A5/A8** `scripts/promote_night_fails.py` → NIGHT_FAIL_PROMOTIONS.md (+ optional stubs)
- **A4** `scripts/portfolio_install_report.py` residual HARNESS_VERSION report (`--install`/`--push` opt-in)
- **A2/B6** `scripts/remaining_board.py` → REMAINING.md
- Docs: ship-flow helpers; release_mgmt post-tag pointers

## v1.4.11 — 2026-08-02

### Added (feedback loop slice 1)
- `scripts/night_shift_morning_triage.py` — multi-product morning FAIL aggregate + optional `--recheck`
- `deploy/morning-triage.{service,timer}` + install dry-run script
- Docs: night-shift.md morning triage section

## v1.4.10 — 2026-07-29

### Added (C5 harden — ticket 03)
- `scripts/agent_eval_checklist.py` skill-conformance runner
- tests + daytime-gates.yml C5 step
- docs/agent-eval-spike.md runner usage

## v1.4.9 — 2026-07-29

### Added (B5 harden — ticket 02)
- hard_gates: `## Evidence pack` required for code ships (≥2 of hard_gates/smoke/pytest/validate/coverage/SBOM)
- PR_DRAFT template + release_mgmt skill wording

## v1.4.8 — 2026-07-29

### Added (A3 harden — ticket 01)
- `deploy/daytime-gates.service` + `.timer` (18:00 UTC multi-product daytime readiness)
- `scripts/install_daytime_timer.sh` (dry-run default, `--apply` enable)
- `scripts/check_daytime_wiring.py` + tests
- `templates/daytime-gates.yml` product GHA template
- Docs: night-shift.md, ship-flow.md

### Fixed
- `start_feature.py` ruff F541 for validate full

## v1.4.7 — 2026-07-29

### Docs / operator front door
- **`/spec` is required for features** (not optional): README, ship-flow, skills-catalog, llm-bootstrap, AGENTS template — Spec path or **Spec waiver** for hotfix/chore/docs.
- **`docs/start-a-feature.md`** + install copy to `.agents/docs/`.
- **`scripts/start_feature.py`** scaffold PR_DRAFT (+ optional spec stub); tests.

## v1.4.6 — 2026-07-29

### Added (ADSLC tickets 01–05)
- **B1** `scripts/spec_gate.py` + execute_dev pre-check
- **B2** Traceability hard gate in `hard_gates.py`
- **A3** `.github/workflows/daytime-gates.yml` + cron docs
- **A4** install `--delete-stale-skills` + `HARNESS_VERSION` + `config/removed_portable_skills.txt`
- **A5** pipeline `spec_id` / `card_id` / `waiver` on `pipeline_state`
- **B3** `scripts/context_pack.py`
- **B4** Threat notes hard gate (runtime)
- **B5** release_mgmt evidence pack notes
- **C1** `/retrospect` skill
- **C2** `tests/test_fsm_conformance.py`
- **C3** `scripts/night_shift_taxonomy.py`
- **C4** qa_campaign only for large post-sync_docs (`--force-qa`)
- **C5** `docs/agent-eval-spike.md`


## Open work

### [DONE] P0 unattended chain + night remediate + default portfolio push
- **Status:** done (v1.4.13)
- **Priority:** P0
- **Next:** false
- **Spec:** `.agents/specs/2026-08-02-p0-unattended-and-remediate.md` (inline ship)
- **Acceptance:**
  - [x] run_ship_chain
  - [x] night_fail_remediate
  - [x] release default portfolio --install --push
- **Smoke:** unittest + product_smoke

### [DONE] P0–P1 feedback loops (finish-ship, promote fails, portfolio, remaining)
- **Status:** done (v1.4.12)
- **Priority:** P0–P1
- **Next:** false
- **Spec:** `.agents/specs/2026-08-02-p0-p1-feedback-loops.md`
- **Plan:** `.agents/specs/2026-08-02-p0-p1-feedback-loops-plan.md`
- **Tickets:** `.agents/specs/2026-08-02-p0-p1-feedback-loops/tickets/`
- **Acceptance:**
  - [x] finish_ship + PUSH_PROOF (A1/A3)
  - [x] promote_night_fails (A5/A8)
  - [x] portfolio_install_report (A4)
  - [x] remaining_board REMAINING.md (A2/B6)
- **Smoke:** unittest + product_smoke
- **Notes:** No LLM auto-skill; install/push opt-in

### [DONE] Night-shift morning triage (feedback loop slice 1)
- **Status:** done (v1.4.11)
- **Priority:** P0
- **Next:** false
- **Spec:** `.agents/specs/2026-08-02-night-shift-morning-triage.md`
- **Plan:** `.agents/specs/2026-08-02-night-shift-morning-triage-plan.md`
- **Tickets:** `.agents/specs/2026-08-02-night-shift-morning-triage/tickets/`
- **Acceptance:**
  - [x] morning_triage script + tests + MORNING_TRIAGE.md
  - [x] optional recheck + timer units dry-run
  - [x] docs
- **Smoke:** unittest + product_smoke
- **Notes:** No auto-ship; aggregate FAIL/TODO after night_shift

### [DONE] ADSLC harden — A3 ops, B5 evidence score, C5 eval runner
- **Status:** done (v1.4.8–v1.4.10)
- **Priority:** P0–P1
- **Next:** false
- **Spec:** `.agents/specs/2026-07-29-adslc-a3-b5-c5-harden.md`
- **Plan:** `.agents/specs/2026-07-29-adslc-a3-b5-c5-harden-plan.md`
- **Tickets:** `.agents/specs/2026-07-29-adslc-a3-b5-c5-harden/tickets/`
- **Acceptance:**
  - [x] A3 daytime systemd + install + wiring check + product GHA template (ticket 01)
  - [x] B5 Evidence pack hard gate (ticket 02)
  - [x] C5 agent_eval_checklist runner (ticket 03)
- **Smoke:** harness unit + hard_gates + check_daytime_wiring + agent_eval_checklist
- **Notes:** Hardens soft gaps from v1.4.6; no new FSM phases

### [DONE] Operator front door — start features with /spec
- **Status:** done (v1.4.7)
- **Priority:** P1
- **Next:** false
- **Spec:** `.agents/specs/2026-07-29-operator-start-feature-front-door.md`
- **Plan:** `.agents/specs/2026-07-29-operator-start-feature-front-door-plan.md`
- **Tickets:** `.agents/specs/2026-07-29-operator-start-feature-front-door/tickets/`
- **Acceptance:**
  - [x] docs/start-a-feature.md + links
  - [x] scripts/start_feature.py + tests
  - [x] install copies doc to products
- **Smoke:** start_feature + spec_gate on temp root
- **Notes:** Ergonomics on top of hard gates / ADSLC; not a new FSM phase


### [DONE] ADSLC A3–A5 + Layer B (B1/B2 P0) + Layer C
- **Status:** done (v1.4.6)
- **Priority:** P0–P2
- **Next:** false
- **Spec:** `.agents/specs/2026-07-29-adslc-a3-a5-layer-b-c.md`
- **Plan:** `.agents/specs/2026-07-29-adslc-a3-a5-layer-b-c-plan.md`
- **Tickets:** `.agents/specs/2026-07-29-adslc-a3-a5-layer-b-c/tickets/`
- **Acceptance:**
  - [x] B1 spec gate + B2 traceability (ticket 01)
  - [x] A3 daytime CI + A4 install delete/stamp + A5 pipeline identity (ticket 02)
  - [x] B3–B5 context/threat/release evidence (ticket 03)
  - [x] C1/C2/C4 retro + self-tests + qa large-only (ticket 04)
  - [x] C3/C5 taxonomy + eval spike (ticket 05)
- **Smoke:** harness unit + hard_gates + daytime_readiness_subset --root .
- **Notes:** Builds on v1.4.5 hard gates; no new FSM phases


## v1.4.5 — 2026-07-29

### Added
- **Hard gates pack** for `/pr_review --validate`: `scripts/hard_gates.py` (CODE-REVIEW, red-proof, BEHAVIOR-REPORT when runtime, Spec/waiver, secrets). Rubric `hard_gates=25` all-or-nothing.
- Spec: `.agents/specs/2026-07-29-hard-gates-pack.md` (+ plan).
- Docs: ship-flow hard gates section; `pr_review` skill updated.

### Changed
- `pr_validator` rubric rebalanced (suite/gate 20 each, section_9 15, hardcode/hygiene 10, hard_gates 25).


## v1.4.4 — 2026-07-29

### Added
- **`/qa_campaign` skill** — full end-to-end autonomous QA + bug hunt + root-cause fix campaign (subagents, worktrees, multi-layer tests, vault report). Protocol in `skills/qa_campaign/references/campaign-protocol.md`.
- **`next_skill.py` after `/sync_docs`:** suggests `NEXT_SKILL=/qa_campaign` (full FSM complete); `--skip-qa` → `(done)`.

### Docs / install
- README, ship-flow, skills-catalog, llm-bootstrap, AGENTS template; `config/ship_skills.txt` includes `qa_campaign` (+ support skills for verify).

## v1.4.3 — 2026-07-28

### Removed
- **`/anti_slop_design` skill** — not required in the portable harness; products that still need UI design law can keep a product-local skill.

### Docs
- **README + ship-flow + skills-catalog + llm-bootstrap + overview** aligned with full FSM: `code_review` / `behavior_validator` / conditional `vps_infra_ops`, `NEXT_SKILL=` router, handoff/session tools, night_shift helpers (`smoke_unit`, daytime readiness, vault group-write).
- Pinned bootstrap tag examples updated to current release series.

## v1.4.2 — 2026-07-28

### Fixed (night_shift readiness)
- Hardcode scanner skips content/secrets/vault/vendored/test-results; product domain allowlists; `--root`.
- Vault normalize ignores epoch `When:`; mojibake headings; multi-job contract retry.
- Vault group-write covers `harness-night-shift` SUMMARY/log.
- `cross_review_gate` accepts legacy 2-tuple mocks (product tests).
- **`daytime_readiness_subset.py`** for pre-night hard gates.

## v1.4.1 — 2026-07-27

### Fixed
- **`scripts/smoke_unit.sh`** — unit smoke without nested `bash -c` (night_shift syntax errors).
- **`vault_fs` + `ensure_vault_group_write`** — group-writable vault logs for night_shift.

## v1.4.0 — 2026-07-26

### Added
- **Any-LLM bootstrap:** `docs/llm-bootstrap.md`, `templates/AGENTS.harness.md`, install `--verify`, `scripts/bootstrap_check.sh`, `config/ship_skills.txt` (ship-chain manifest).
- **`verify_skills.py`:** dual-root (harness `skills/` or product `.agents/skills/`); require ship-chain skills; works after install.
- **Tests:** `tests/test_install_bootstrap.py`, `tests/test_verify_skills.py` (stdlib unittest; temp product install).
- Install copies `.agents/docs/{ship-flow,skills-catalog,llm-bootstrap,bootstrap}.md` into products.

### Added (earlier unreleased)
- **Night shift dev-deps preflight:** `scripts/ensure_product_dev_env.py` + multi-product orchestrator preflight before readiness (venv + requirements-dev; no sudo pip).

- **Night-shift log template:** canonical vault `night-shift-log.md` (Timeline newest-first + dual UTC/HKT + full reports). Helpers in `scripts/night_shift_log.py`; readiness prepend + rotate share the same render. Spec: `docs/specs-2026-07-18-night-shift-log-template.md`.

- **`/night_shift`** (finished feature): multi-product overnight readiness SoT.
  - Skill `skills/night_shift/`, `scripts/night_shift_readiness.py`, `scripts/check_test_matrix.py`
  - Orchestrator `bin/night_shift_all_products.py` + `config/night_shift_products.yaml`
  - systemd `deploy/night-shift-all.{service,timer}` — **03:15 HKT** (19:15 UTC)
  - Vault: per-product `TODO.md` + `night-shift-log.md`; multi summary under `harness-night-shift/`
  - Coverage gate (ORCH-P3b): `check_module_coverage.py` + example config; soft-if-missing for night runs
  - `tools/bin/lint_and_test.sh` installed into products via `install_into_product.sh`
  - Hard-stops: no auto-ship, no auto product code fixes
  - **Docs:** full operator manual [`docs/night-shift.md`](docs/night-shift.md); linked from README, ship-flow, product-plugin, vault optional
- **`/anti_slop_design`** skill: full [pols.dev anti-slop design law](https://pols.dev/slop.md) as a harness skill (`skills/anti_slop_design/`). Mandatory confirm → build → point-by-point pre-ship re-check for any UI work. Law body + `references/slop.md` mirror.

### Changed
- Vault / second-brain integration is **optional and off by default** (public harness stays vault-agnostic).
- SoT for skills/policies documented (`docs/source-of-truth.md`).
- Optional vault adapter docs (`docs/second-brain-optional.md`); `scripts/vault_resolve.py`.
- Removed hardcoded `/opt/second-brain` and watchlist-only paths from portable sync scripts/skills.
- **PR_DRAFT template:** narrative sections **What Problem This Solves**, **Why This Change Was Made**, **User Impact**, **Evidence** (plus existing Red-proof / Cross-review / §9). Wired into `AGENT_WORKFLOW` Phase 5, `execute_dev` handoff, `pr_review` soft check, `base_constraints`, `docs/ship-flow.md`.

## v1.2.0 — 2026-07-15

- **`/spec` v2:** constitution read (`.agents/CONSTITUTION.md` / AGENTS.md / policy), structured **clarify** pass, optional **`--plan`** technical plan file, Spec Kit **bridge notes** (detect `.specify/` only — no install)
- Templates: `templates/CONSTITUTION.example.md`; `skills/spec/references/{plan-template,clarify-checklist,speckit-bridge}.md`
- Docs: skills catalog + ship flow updated

## v1.1.0 — 2026-07-15

- **Portable skill `/spec`**: interview or synthesize → `.agents/specs/` + product-roadmap OPEN item for `/execute_dev` (Finn Loop + Matt Pocock patterns; optional Linear/GitHub/tickets)
- Depth: `skills/spec/references/spec-template.md`, `provenance.md`
- Docs: ship flow, skills catalog, README include `/spec` as front door of the ship loop
- No new scripts or runtime deps (optional `gh` / Linear only when flags used)

## v1.0.0 — 2026-07-13

First **stable public bootstrap**.

- Portable skills: execute_dev (TDD), pr_review, cross_review, release_mgmt, sync_docs, sweep, feedback, audit_repo, plan_backend, test_automation  
- Scripts: pipeline FSM, validate stack, PR score, soft cross-review gate, vault note/release, worksheets  
- Policy pack + product plugin example (stack-agnostic)  
- `install_into_product.sh`  
- Docs structured for progressive disclosure (bootstrap → plugin → ship → TDD → writing skills)  
- Extracted from production use; **no product application code** in this repo  
