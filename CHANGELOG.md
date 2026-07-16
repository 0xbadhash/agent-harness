# Changelog

## Unreleased

### Changed
- Vault / second-brain integration is **optional and off by default** (public harness stays vault-agnostic).
- SoT for skills/policies documented (`docs/source-of-truth.md`).
- Optional vault adapter docs (`docs/second-brain-optional.md`); `scripts/vault_resolve.py`.
- Removed hardcoded `/opt/second-brain` and watchlist-only paths from portable sync scripts/skills.


## Unreleased

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
