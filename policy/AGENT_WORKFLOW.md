# AGENT_WORKFLOW.md — Agentic session workflow (meta)

**Not the product.** Product guide: `docs/PRODUCT.md`. Boundary: `docs/PRODUCT_BOUNDARY.md`. Harness home: `.agents/README.md`.

**Dense summary:** Research → Plan → Implement (TDD + **run the app**) → Test → Cross-Review → Vault log → Feedback. Router: root `GEMINI.md` + vault `AGENTS.md`. Pipeline FSM: `.agents/state/pipeline.json`.

## Precedence

1. `ENGINEERING_ASSURANCE.md` (policy)
2. `GEMINI.md` (routing / file boundaries)
3. `AGENTS.md` (Obsidian vault logging for agents)
4. This file (session phases)
5. Skill `SKILL.md` for the active gate

## Phase checklists

### Phase 1 — Research
- [ ] Classify: **product** change vs **harness-only** (see `docs/PRODUCT_BOUNDARY.md`)
- [ ] Read `AGENTS.md` (vault) + `GEMINI.md` (route) + `.agents/README.md`
- [ ] Grep/search before full-file reads on large sources
- [ ] Worksheet (optional): `python3 scripts/generate_worksheet.py --task-id <id> --title "..."` → `.agents/traces/`
- [ ] Note findings under worksheet **Steps** / **Issues**

### Phase 2 — Plan
- [ ] Product tasks: acceptance in `BACKEND_ROADMAP.md` (product only)
- [ ] Harness tasks: `.agents/BACKLOG.md` (not product Shaping)
- [ ] High-risk changes: human approval gate
- [ ] Single sub-task only (no multi-epic cycles)

### Phase 3 — Implement (TDD + run the app)
- [ ] **TDD mandatory for code:** failing tests first (Red), then Green, then Refactor — see `/execute_dev` step 3
- [ ] Prove Red by running tests before implementation completes
- [ ] Surgical diffs only
- [ ] **Principle 3 — Run the app** after significant change:
  - PHP/web: `cd migration && php bin/health.php` (exit 0)
  - Risk/API: relevant PHPUnit or `risk=` endpoint smoke
  - UI/JS: `node migration/tests/<area>.test.js` + hard-refresh mental check
  - Python tooling: `PYTHONPATH=. .venv/bin/python -m pytest -q <tests>`
- [ ] Fix observed failures before handoff

### Phase 4 — Test & validate
- [ ] Diff-first: `python3 scripts/validate.py full`
- [ ] Hygiene / hardcodes as required by skill
- [ ] False-confidence audit: tests hit public contract, not only mocks

### Phase 5 — Cross-review (when non-trivial / large)
- [ ] Invoke `/cross_review` **before** `/pr_review` when diff is large
- [ ] Fill `PR_DRAFT.md` from `templates/PR_DRAFT.md` narrative sections:
  - **What Problem This Solves** · **Why This Change Was Made** · **User Impact** · **Evidence**
  - Plus **Red-proof**, **Cross-review**, **Test plan**, §9 (min 3)
- [ ] Record `## Cross-review` in `PR_DRAFT.md` or `.agents/artifacts/CROSS_REVIEW.md`
- [ ] Soft gate: `python3 scripts/cross_review_gate.py --diff <range>` (warn only)
- [ ] Personas: Security · Maintainability · Domain (product-specific)

### Phase 6 — Self-heal & document
- [ ] Update only files allowed by skill Writes line
- [ ] Vault: `dev-log.md` per `AGENTS.md` (unless ephemeral)
- [ ] Decisions → vault `decisions.md` or repo design docs

### Phase 7 — Feedback
- [ ] Append session notes to `AGENT_FEEDBACK.md` via `/feedback` skill
- [ ] Pipeline phase advanced only by skill scripts (`pipeline_state.py`)

## Pipeline skills (quick map)

| Phase / intent | Skill |
|----------------|--------|
| Implement | `/execute_dev` |
| Compliance score | `/pr_review --validate` |
| Infra verify | `/vps_infra_ops --verify` |
| Tag & smoke | `/release_mgmt` |
| Docs + vault release | `/sync_docs` |
| Multi-persona review | `/cross_review` |
| Hygiene sweep | `/sweep` |
| Session feedback | `/feedback` |

## Anti-patterns

See `docs/AGENT_REFERENCE.md`. Never skip phase gates or invent dual routers.
