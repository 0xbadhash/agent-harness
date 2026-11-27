# PR Draft: Harness top-50 completion — decisions, prototype, review rigor, retro, stacked execution

**Range:** `origin/main...HEAD`

**Spec:** `.agents/specs/2026-11-27-harness-top50-completion.md`
**Plan:** `.agents/specs/2026-11-27-harness-top50-completion-plan.md`
**Tickets:** `.agents/specs/2026-11-27-harness-top50-completion/tickets`

## What Problem This Solves

Thirty-five improvements from the 2026-11-21 harness scorecard were still prose
or absent. Operators lost decisions between sessions, shape questions were settled
by debate, review depth was flat, retros did not read their own evidence, and a
large stack needed manual merging and ticket-by-ticket babysitting.

## Why This Change Was Made

The first fifteen scorecard items shipped in v1.4.57. The remainder is mostly
independent and already has partial helpers (`prototype_variants.py`,
`agent_transcript.py`, `check_comment_audit.py`, `session_context.py`,
`context_pack.py`, `stack_plan.py`). This ship wires those helpers and adds the
missing gate or template beside each one, so every item becomes checkable instead
of advisory prose.

## User Impact

- `/spec` reads ADRs, records reserved versus delegated decisions, offers
  prototype variants for shape questions, writes a compact grill handoff, and can
  run a read-only research subagent.
- Review reports a comment ratio, adds a Process lens, and requires a
  reproduction for defect fixes; the PR template carries door-aware fields.
- Retro ingests local transcripts and PR comments and classifies findings.
- `merge_stack.py` and `run_tickets.py` land a stack in order and run the
  unblocked frontier in parallel.
- Feature flags are required for user-visible large ships; token and context cost
  are recorded per ship.

## Evidence

- `python3 -m pytest tests/ -q`
- `python3 scripts/validate.py full`
- `python3 scripts/hard_gates.py --diff origin/main...HEAD`
- `python3 scripts/product_smoke.py --root .`
- `python3 scripts/check_ticket_dag.py .agents/specs/2026-11-27-harness-top50-completion/tickets`
- `python3 scripts/stack_plan.py --tickets .agents/specs/2026-11-27-harness-top50-completion/tickets`
- `python3 scripts/check_adr.py --root .`
- `python3 scripts/check_docs_patterns.py --root .`
- `python3 scripts/check_comment_audit.py --diff origin/main...HEAD --strict`

## Merge Danger

**Door:** one-way
**Blast Radius:** Harness-wide. Every skill and several gates change, and the
agent-harness PR also adds new scripts. Reverting is a normal revert of the squash
commit, but a partial revert leaves skills pointing at commands that no longer
exist.

## Threat notes

- **Assets:** the harness itself, tokens and session paths read by the cost and
  transcript helpers, and the operator's PRs that the stack merger acts on.
- **Abuse cases:** a crafted ticket or transcript injects secrets into an
  artifact; a stack runner merges a PR whose checks are red; an ADR check is
  passed by a placeholder body. The ingest path redacts secret-like lines, the
  merger stops on any non-success check, and the ADR check requires all three
  parts.
- **Boundaries:** no new network calls in the default path; `--gh` stays behind an
  explicit flag; auto-merge stays opt-in.

## Traceability

| AC | Test / command |
|----|----------------|
| AC-1 | `tests/test_decisions_and_review.py`, `scripts/check_adr.py`, `scripts/check_ticket_dag.py` |
| AC-2 | `tests/test_prototype_and_handoff.py`, `scripts/check_prototype_fidelity.py` |
| AC-3 | `tests/test_comment_and_docs.py`, `scripts/check_comment_audit.py --ratio` |
| AC-4 | `tests/test_retro_ingest.py`, `scripts/retro_job.py --transcripts` |
| AC-5 | `tests/test_stack_runners.py`, `scripts/merge_stack.py`, `scripts/run_tickets.py` |
| AC-6 | workflow-harness `pytest`, `scripts/check_canary.py` |
| Smoke | `python3 scripts/validate.py full`, `bash scripts/smoke_unit.sh` |

## Red-proof

Red: `git cat-file -e origin/main:scripts/check_adr.py` (exit 128 — the checker
does not exist on the base).
Green: `python3 -m pytest tests/test_decisions_and_review.py -q` after the change.

## Evidence pack

- hard_gates: run on `origin/main...HEAD` before review.
- pytest: full suite plus the four new test modules.
- validate: `python3 scripts/validate.py full` (ruff, mypy, tests).
- smoke: `python3 scripts/product_smoke.py --root .`.
- ticket DAG: 19 tickets, valid, ready frontier recorded.

## Things that look bad but are actually fine

- The diff is large. It is one epic with a ticket per scorecard item and a
  chunked review; each chunk maps to a batch.
- Several checks are advisory unless `--strict` is passed. That keeps product
  repos without a declared surface from failing on fields they do not use; this
  repo runs them with `--strict`.
- `retro_job.py` reads local session files best-effort. When nothing is found it
  writes `unknown` rather than failing the retro.
- The workflow-harness changes ship in a separate PR so the two suites stay
  independent.
