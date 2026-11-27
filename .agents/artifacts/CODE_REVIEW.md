# Code review — harness top-50 completion epic

**Marker:** CODE-REVIEW
**Command:** `/code_review` closeout pass, chunked A–F
**Base:** `origin/main` (`6f962df`, release v1.4.57)
**Head:** `HEAD` (6 commits)
**Scope:** 68 files, +3,121 / −208, non-test LOC ~1,900; large diff

## Standards

Reviewed against the repo style (typed Python, deterministic scripts, no host
paths, one check per accepted finding) and the Fowler baseline:

- `Mysterious Name` — none. `check_adr`, `check_prototype_fidelity`,
  `merge_stack`, `run_tickets` name their effect.
- `Duplicated Code` — `run_tickets` imports `check_ticket_dag`; `merge_stack`
  imports `stack_plan`; `retro_runs` reuses `framework/retro.py` in the
  companion. No second DAG parser or scoring model in this tree.
- `Feature Envy` — the reviewer tier lives in `spec_gate` because it already
  reads the plan and the door; no new module for one helper.
- `Data Clumps` — ticket fields stay a dict because the on-disk format is
  Markdown with `**Field:**` lines.
- `Primitive Obsession` — ticket ids stay strings; the numeric prefix is the
  identity.
- `Repeated Switches` — the review tier is one table in `pr_review`, not a
  branch per door.
- `Shotgun Surgery` — each skill edit is one stage block; no cross-cutting
  rewrite.
- `Speculative Generality` — every new flag has a test, and `--default-estimate`
  exists because a ticket may omit the field.

Verdict: pass. No standing refactor required.

## Spec

- **AC-1 (decisions/doors):** `.agents/decisions/README.md`,
  `000-template.md`, `001-review-tiers-by-door.md`, `scripts/check_adr.py`,
  `tests/test_decisions_and_review.py`.
- **AC-2 (prototype and handoff):** `skills/prototype/SKILL.md`,
  `scripts/check_prototype_fidelity.py`, `context_pack.py --compact`
  (`GRILL_HANDOFF.md`), `tests/test_prototype_and_handoff.py`.
- **AC-3 (review rigor):** `.agents/policy/comment-policy.md`,
  `skills/comment_audit/SKILL.md`, `check_comment_audit.py --ratio`,
  `templates/eslint-ratchet/`, `docs/tdd.md`, `scripts/session_context.py`
  (`SESSION_COST.md`), `skills/handoff/SKILL.md`, `skills/cross_review/SKILL.md`
  (Process lens), `scripts/check_docs_patterns.py`,
  `tests/test_comment_and_docs.py`.
- **AC-4 (retro):** `scripts/retro_job.py --transcripts/--pr-comments`, five
  action classes, `skills/retrospect/SKILL.md`,
  `tests/test_retro_ingest.py`.
- **AC-5 (stacked execution):** `scripts/merge_stack.py`,
  `scripts/run_tickets.py`, `skills/release_mgmt/SKILL.md`,
  `tests/test_stack_runners.py`.
- **AC-6 (workflow companion):** PR #13 in workflow-harness
  (`specs/adr/`, `framework/tickets.py`, `framework/canary.py`,
  `tools/check_adr.py`, `check_canary.py`, `check_ticket_order.py`,
  `retro_runs.py`), 212 tests green there.

Scope creep: none. The two P2 follow-ups from v1.4.57 are closed by E3
(`--default-estimate`) and the ticket-root CI change.

## Findings

1. **P1 — ticket DAG reported a false cycle** on the real epic (11→07,08→07).
   The DFS never popped its stack. Accepted and fixed with a color-state DFS;
   `tests/test_decisions_and_review.py::test_ticket_dag_accepts_a_diamond`
   covers the diamond.
2. **P2 — CI ticket step scanned one root.** Accepted and fixed: the workflow
   globs `.agents/specs/*/tickets` and honours a configured root.
3. **P2 — LOC estimate was hard-coded 150.** Accepted and fixed:
   `stack_plan.py` reads `**Estimate:**` and takes `--default-estimate`.
4. **Pre-commit gate findings (not review findings, recorded for honesty):**
   an unused variable in `check_adr.py`, `shell=True` in `run_tickets.py`, and
   two mypy narrowing errors. All fixed before the review commit; `ruff`,
   `mypy`, and the lint ratchet are green.

P0 count: 0. Open follow-ups: 0.

## Review chunks

- **A (tickets 01–03):** ADR spine, review tiers, prefactor. Pass after the
  false-cycle fix.
- **B (04–06):** prototype, grill handoff, modes/data model. Pass.
- **C (07–11):** comment policy, ratchet, cost/handoff, process lens, docs
  sweep. Pass.
- **D (12–13):** retro ingest and action classes. Pass.
- **E (14–16):** merge stack, ticket runner, P2 fixes. Pass.
- **F (17–19, companion):** workflow-harness PR #13. Pass; its own CI is
  authoritative for that tree.

## Evidence

- Tests: `python3 -m pytest tests -q` → **584 passed, 3 skipped**.
- Validate: `python3 scripts/validate.py full` → **9/9 gates**.
- Compliance: type_checker, linter, test_runner all exit 0.
- Smoke: `python3 scripts/product_smoke.py --root .` → 2/2.
- ADR: `check_adr.py --root . --strict` → 1 ADR indexed and complete.
- Docs patterns: `check_docs_patterns.py --root .` → clean.
- Ticket DAG: 19 tickets valid; frontier `01, 07, 10, 12, 16, 17`.
- Stack plan: 3 layers / 3 chunks written to `.agents/artifacts/STACK_PLAN.md`.
- Comment audit: `check_comment_audit.py --diff origin/main...HEAD --strict` → clean.
- Secrets: `check_secrets_diff.py --base origin/main --head HEAD` → clean.
- Companion: workflow-harness suite 212 passed; its three new gates green.

## Correction checks

- P1 the ticket DAG reported a false cycle → tests/test_decisions_and_review.py::test_ticket_dag_accepts_a_diamond
- P2 CI scanned one ticket root → tests/test_stack_runners.py::test_ci_scans_every_ticket_root
- P2 the LOC estimate was hard-coded → tests/test_comment_and_docs.py::test_stack_plan_default_estimate_is_configurable
- A gate could pass on a placeholder ADR → scripts/check_adr.py --strict (three-part test)
- A prototype could be copied instead of referenced → tests/test_prototype_and_handoff.py::test_copied_prototype_code_fails
- A retro could leak a secret from a transcript → tests/test_retro_ingest.py::test_transcripts_redact_secret_like_lines
- A PR comment could leak a secret into an issue body → tests/test_retro_ingest.py::test_pr_comments_are_redacted_too
- A stack merge could proceed on a red PR → tests/test_stack_runners.py::test_merge_stops_when_a_check_is_red

## Handoff

CODE-REVIEW DONE  p0=0  follow_ups=0
NEXT_SKILL=/cross_review
