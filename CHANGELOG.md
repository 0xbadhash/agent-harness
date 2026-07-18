# Changelog

## Unreleased

### Planned
- **Night shift dev-deps preflight (OPEN):** ensure product `.venv` + requirements-dev before multi-product readiness. Spec: `docs/specs/2026-07-18-night-shift-dev-deps-preflight.md`.

### Added
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
