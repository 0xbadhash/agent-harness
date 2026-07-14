# Changelog

## Unreleased

- **PR_DRAFT template:** narrative sections **What Problem This Solves**, **Why This Change Was Made**, **User Impact**, **Evidence** (plus existing Red-proof / Cross-review / §9). Wired into `AGENT_WORKFLOW` Phase 5, `execute_dev` handoff, `pr_review` soft check, `base_constraints`, `docs/ship-flow.md`.

## v1.0.0 — 2026-07-13

First **stable public bootstrap**.

- Portable skills: execute_dev (TDD), pr_review, cross_review, release_mgmt, sync_docs, sweep, feedback, audit_repo, plan_backend, test_automation  
- Scripts: pipeline FSM, validate stack, PR score, soft cross-review gate, vault note/release, worksheets  
- Policy pack + product plugin example (stack-agnostic)  
- `install_into_product.sh`  
- Docs structured for progressive disclosure (bootstrap → plugin → ship → TDD → writing skills)  
- Extracted from production use; **no product application code** in this repo  
