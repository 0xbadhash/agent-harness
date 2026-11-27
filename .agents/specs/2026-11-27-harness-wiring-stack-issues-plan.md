# Plan: Wire harness helpers, tighten spec rituals, plan stacked ships

- **Spec:** `.agents/specs/2026-11-27-harness-wiring-stack-issues.md`
- **Product:** agent-harness
- **Created:** 2026-11-27
- **Status:** ready-for-agent

## Stack & constraints

- Python 3.13 in the repo venv, pytest, ruff, mypy through `compliance_engine`.
- Harness-only changes under `scripts/`, `skills/`, `.github/`, and tests.
- `workflow-harness` is a separate git tree; its data and tests ship there.
- No network calls in the default path. `gh` requires `--gh`.

## Approach

Keep the five helpers as they are and add invocations where their stage runs.
Add one deterministic planner for stack layers and reuse its output in review
chunking. Extend `retro_job.py` with an offline issue-body writer. Extend the
spec checklists and the glossary gate. Add the `workflow-harness` data files and
a small validation test.

## Architecture decisions

- `scripts/stack_plan.py` reads tickets through `check_ticket_dag.load_tickets`,
  so cycle detection and layer ordering share one parser.
- Issue bodies are files first; `gh` is a thin adapter behind a flag.
- `spec_gate.py` normalizes glossary terms to `[a-z0-9]` keys for collision
  detection and keeps the existing uppercase-term resolution check.
- Skill changes are prose contracts with exact commands, not new code paths.

## File / surface map (indicative)

| Area | Change |
|------|--------|
| `skills/execute_dev/SKILL.md` | Ticket DAG, smart zone, compact safety, stack plan |
| `skills/code_review/SKILL.md` | Comment audit and per-layer review chunks |
| `skills/retrospect/SKILL.md` | Retro job and issue-body filing |
| `skills/spec/SKILL.md` + references | Stop token, why-first, pain ranking, name scenarios |
| `scripts/spec_gate.py` | Glossary collision check |
| `scripts/retro_job.py` | `--file-issues`, `--gh`, umbrella issue |
| `scripts/stack_plan.py` | New layer/chunk planner |
| `.github/workflows/daytime-gates.yml` | Comment audit and ticket DAG steps |
| `workflow-harness/glossary.json` | New domain dictionary |
| `workflow-harness/tickets/*.md` | Acceptance criteria and blocking edges |

## Implementation sequence

1. Add failing tests for wiring contracts, the glossary collision gate, issue
   bodies, and stack layers.
2. Implement `scripts/stack_plan.py` and the `spec_gate.py` collision check.
3. Extend `retro_job.py` with offline issue bodies and the guarded `gh` path.
4. Update the five owning skills and the CI workflow.
5. Add the `workflow-harness` glossary, normalize its tickets, and run its tests.
6. Run the harness suite, smoke, review, behavior, and release gates.

## Testing plan

- `tests/test_harness_wiring_stack.py` covers AC-1 through AC-5 for the harness.
- `workflow-harness/tests/test_glossary_and_tickets.py` covers the glossary
  schema and ticket fields.
- CLI checks: `retro_job.py --file-issues`, `stack_plan.py --write`,
  `spec_gate.py` on a fixture with a collision, `check_ticket_dag.py`.
- Smoke: `python3 scripts/product_smoke.py --root .`.

## Risks & mitigations

| Risk | Mitigation |
|------|------------|
| Duplicate glossary rows legitimately share a word | Compare normalized full terms and report both rows |
| Issue bodies leak secrets | Reuse `check_secrets_diff.py` before `--gh`; default offline |
| Stack layers hide a cycle | Reuse `check_ticket_dag.find_cycle` and exit 1 |
| Skill edits drift from scripts | Tests assert exact commands appear in the skill text |

## Open questions

None.
