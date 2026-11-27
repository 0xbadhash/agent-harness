# Plan: Harness top-50 completion

- **Spec:** `.agents/specs/2026-11-27-harness-top50-completion.md`
- **Product:** agent-harness
- **Created:** 2026-11-27
- **Status:** ready-for-agent
- **Tickets:** `.agents/specs/2026-11-27-harness-top50-completion/tickets`

## Stack & constraints

- Python 3.12, pytest, ruff, mypy via `scripts/validate.py`.
- Markdown skills under `skills/`; templates under `skills/spec/references/` and
  `templates/`.
- Harness-only change: no product tree, no runtime dependencies.
- One agent-harness PR plus one workflow-harness PR; review is chunked by batch.

## Approach

Reuse the helpers that already exist but are unwired. Each ticket adds the
smallest gate that makes its scorecard item observable: a parser plus an exit
code, a template field plus a checker, or a skill rule that names an existing
command. Where an item is advisory for repos without a product surface, the
checker reports and exits 0 unless `--strict` is passed.

## Architecture decisions

- **Decisions:** `.agents/decisions/` holds one Markdown ADR per file with a
  `# ADR NNN` header and a three-part body (reversibility, surprise, tradeoff);
  `README.md` is the index. `check_adr.py` validates the index and the three
  parts, and refuses an ADR that states none of them.
- **Prototype:** `prototype_variants.py` stays the generator. A new
  `check_prototype_fidelity.py` reads the spec's `**Prototype verdict:**` and the
  deleted-variant marker; copied prototype code is a failure.
- **Review tiers:** the existing `**Door:**` field selects a tier table in
  `pr_review`; one-way doors additionally require a rollout and rollback line.
- **Comment policy:** `.agents/policy/comment-policy.md` sets a phased scope
  (one directory allowlist) and points at `check_comment_audit.py`; the skill is a
  thin wrapper so the command stays single-sourced.
- **Token cost:** `session_context.py` reads local session files when present and
  otherwise emits `unknown`; it never invents counts.
- **Stack merge:** `merge_stack.py` reuses `stack_plan.build_plan` for order and
  `gh pr view --json` for state; `--auto-merge` is opt-in.
- **Ticket runner:** `run_tickets.py` reuses `check_ticket_dag.load_tickets` and
  `ready_frontier`, and writes one worktree per ticket.
- **Explicit non-decisions:** no hosted queue, no new model provider, no change
  to the existing hard-gate rubric weights.

## File / surface map (indicative)

| Area | Change |
|------|--------|
| `.agents/decisions/` | index, template, first ADR |
| `.agents/policy/comment-policy.md` | phased comment policy |
| `scripts/check_adr.py` | new validator |
| `scripts/check_prototype_fidelity.py` | new checker |
| `scripts/check_docs_patterns.py` | new checker |
| `scripts/merge_stack.py`, `scripts/run_tickets.py` | new runners |
| `scripts/check_comment_audit.py` | `--ratio`, baseline output |
| `scripts/check_ticket_dag.py` | prefactor rule, multi-root scan |
| `scripts/stack_plan.py` | `--default-estimate` |
| `scripts/context_pack.py` | `--compact` grill handoff |
| `scripts/session_context.py` | token/context/cost lines |
| `scripts/retro_job.py` | `--transcripts`, `--pr-comments`, action classes |
| `scripts/spec_gate.py` | decision fields, feature-flag field |
| `skills/spec/`, `skills/prototype/`, `skills/comment_audit/` | rules and new skills |
| `skills/pr_review/`, `skills/code_review/`, `skills/cross_review/`, `skills/handoff/`, `skills/execute_dev/`, `skills/retrospect/` | tier, ratio, process, threshold, ingest |
| `templates/PR_DRAFT.md`, `templates/eslint-ratchet/` | prototype/door/flag fields, JS ratchet |
| `.github/workflows/daytime-gates.yml` | ticket roots, docs-pattern step |
| workflow-harness | ADR, retro, canary, ordered stack |

## Implementation sequence

1. Batch A — decisions, review tiers, prefactor rule (tickets 01–03).
2. Batch B — prototype, grill handoff, research subagent, grill modes (04–06).
3. Batch C — comment policy and ratio, JS ratchet, cost, process lens, repro,
   docs sweep (07–11).
4. Batch D — retro transcript and PR-comment ingest, action classes (12–13).
5. Batch E — stack merge, parallel ticket runner, P2 fixes (14–16).
6. Batch F — workflow-harness companion (17–19).
7. Validation and ship FSM.

## Testing plan

- Each script gets a focused pytest module under `tests/`; the epic's ticket DAG
  and stack plan are run against its own tickets.
- `python3 scripts/validate.py full` and `scripts/smoke_unit.sh` gate the ship.
- Runners get `--dry-run` tests; no live merge in tests.

## Risks & mitigations

| Risk | Mitigation |
|------|------------|
| Policy prose without enforcement | Every rule names a script or gate; tests assert the command |
| Advisory gates hide regressions | `--strict` mode used in this repo's CI |
| Stack runner merges out of order | Reuses `stack_plan` layers; stops on first failure |
| Token counts unavailable locally | Emit `unknown`, never fabricate |
| workflow-harness checkout dirty | New worktree from `origin/main` |

## Open questions

None.
