# Changelog

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

### [OPEN] Operator front door — start features with /spec
- **Status:** open
- **Priority:** P1
- **Next:** true
- **Spec:** `.agents/specs/2026-07-29-operator-start-feature-front-door.md`
- **Plan:** `.agents/specs/2026-07-29-operator-start-feature-front-door-plan.md`
- **Tickets:** `.agents/specs/2026-07-29-operator-start-feature-front-door/tickets/`
- **Acceptance:**
  - [ ] docs/start-a-feature.md + links
  - [ ] scripts/start_feature.py + tests
  - [ ] install copies doc to products
- **Smoke:** start_feature + spec_gate on temp root
- **Notes:** Ergonomics on top of hard gates / ADSLC; not a new FSM phase


### [OPEN] ADSLC A3–A5 + Layer B (B1/B2 P0) + Layer C
- **Status:** done (v1.4.6)
- **Priority:** P0–P2
- **Next:** false
- **Spec:** `.agents/specs/2026-07-29-adslc-a3-a5-layer-b-c.md`
- **Plan:** `.agents/specs/2026-07-29-adslc-a3-a5-layer-b-c-plan.md`
- **Tickets:** `.agents/specs/2026-07-29-adslc-a3-a5-layer-b-c/tickets/`
- **Acceptance:**
  - [ ] B1 spec gate + B2 traceability (ticket 01)
  - [ ] A3 daytime CI + A4 install delete/stamp + A5 pipeline identity (ticket 02)
  - [ ] B3–B5 context/threat/release evidence (ticket 03)
  - [ ] C1/C2/C4 retro + self-tests + qa large-only (ticket 04)
  - [ ] C3/C5 taxonomy + eval spike (ticket 05)
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
