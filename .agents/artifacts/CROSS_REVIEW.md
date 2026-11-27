# Cross-review — harness top-50 completion epic

**Marker:** CROSS-REVIEW
**Base:** `origin/main` (`6f962df`)
**Head:** `HEAD`
**Scope:** six commits across `scripts/`, `skills/`, `templates/`, `docs/`,
`.agents/decisions/`, `.agents/policy/`, CI, and five new test modules; plus the
workflow-harness companion PR #13.

## Security Guru

Findings: none blocking.

- `retro_job.py` replaces `AKIA…`, `ghp_…` and `xox…` tokens (and drops a PEM
  begin line) before any transcript or PR-comment text reaches the retro or an
  issue body. Fixtures assert the secret is absent from both paths.
- `merge_stack.py` shells to `gh` with an argv list and stops on any check that
  is not `SUCCESS`/`SKIPPED`/`NEUTRAL`; it never opens a shell with ticket text.
- `run_tickets.py` now splits the executor command with `shlex` and runs it in a
  fresh worktree; `shell=True` is gone (the lint ratchet caught it).
- `check_adr.py`, `check_docs_patterns.py`, `check_prototype_fidelity.py` read
  files under the repo root only and make no network call.
- No new credential, absolute home path, or token is written by the new code.

## Maintainability Expert

Findings: none blocking.

Scoped obsolete/cleanup scan (touched paths plus direct callers):

| Tier | Item | Evidence | Confidence |
|------|------|----------|------------|
| A | none | each new symbol is used by `main()` or a test | 0.9 |
| B | none | `context_pack` keeps its old full-pack path; `--compact` is additive | 0.9 |
| C | `retro_job` action mapping is label-based | unknown labels fall back to `non-action`; the class list is closed | 0.85 |

- Coupling stays one-way: `run_tickets` → `check_ticket_dag` → `stack_plan`;
  `merge_stack` → `stack_plan`. No reverse imports.
- The DAG parser exists once. The retro renderer exists once
  (`framework/retro.py` in the companion); `retro_runs.py` composes it.
- No dead branch: `--compact`, `--ratio`, `--transcripts`, `--pr-comments`,
  `--auto-merge`, `--default-estimate` each have a test.

## Domain Specialist

Findings: none.

- The review tier table matches the door taxonomy used in the plan and the PR
  template: two-way = agent gates plus the auto path; one-way = named human plus
  a rollout/rollback note.
- The prefactor rule matches the ticket format and turns a shared-component
  ticket into a real blocking edge.
- The five retro action classes match the checklist in `skills/retrospect`.
- The companion canary rule matches the scorecard's "run both side by side,
  compare, then promote": `hashes_match` is mandatory and a count of runs alone
  never promotes.
- The ordered stack matches the video's two-way doors ending in a one-way
  registry change.

## Process lens

- Sessions: one long session (this one); no mid-epic handoff.
- Review cycles: one chunked pass. The self-review found the false-cycle bug,
  the two P2s, and three pre-commit gate issues; all fixed with a named check.
- Retries: the compliance engine ran twice (type/lint), then green.
- Handoffs: none during implementation.
- Remaining risk: advisory gates (flag, cost, comment ratio) become hard only
  with `--strict`, which this repo uses. Documented in the plan.

## Verdict

No P0/P1 cross-review findings. Proceed to behavior validation.
NEXT_SKILL=/behavior_validator
