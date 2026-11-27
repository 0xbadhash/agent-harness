# Behavior report — harness top-50 completion

**Marker:** BEHAVIOR-REPORT
**Contract:** `.agents/artifacts/BEHAVIOR_CONTRACT.md`
**Date:** 2026-11-27
**Method:** source-blind CLI runs on the ship tree plus the named tests. No
implementation file was read to decide pass/fail.

| Clause | Result | Evidence |
|--------|--------|----------|
| B1 ADR spine | pass | `check_adr.py --root . --strict` → 1 ADR indexed and complete. Fixtures: missing tradeoff, missing index row, empty spine advisory. |
| B2 Prototype fidelity | pass | `check_prototype_fidelity.py --root .` → N/A (no field). A copied variant fails in `test_copied_prototype_code_fails`. |
| B3 Compact handoff | pass | `context_pack.py --compact --spec <epic>` wrote `GRILL_HANDOFF.md` with decisions, ownership, glossary changes, ADR links and open questions. |
| B4 Comment ratio | pass | `check_comment_audit.py --diff origin/main...HEAD --strict` → no findings. Ratio counts covered by `test_comment_ratio_counts_only_comments_and_code`. |
| B5 Docs patterns | pass | `check_docs_patterns.py --root .` → no rejected patterns taught. A teaching line fails while a retired-note line passes. |
| B6 Session cost | pass | `test_session_cost_is_unknown_until_recorded` and `test_session_cost_markdown_is_written` cover the artifact and the `unknown` default. |
| B7 Retro ingest | pass | `retro_job.py --pr-comments /tmp/retro-fixture/comments.json` → retro written, `ghp_` count 0, `[redacted]` present, action classes `non-action` and `add-gate`. |
| B8 Merge stack | pass | `merge_stack.py --dry-run` printed `would merge <tid>` for every ticket in layer order; `test_merge_stops_when_a_check_is_red` covers the stop. |
| B9 Ticket runner | pass | `run_tickets.py --dry-run` printed `would run` for each frontier ticket; dependents are blocked after a failure, and session ids are recorded only on a real run. |
| B10 Spec gate | pass | `spec_gate.py --strict` → spec, 7 Q/A grill, 19 tickets, reserved/delegated, 5 data-model terms, all N/A checks explicit. |
| B11 Stack plan | pass | `stack_plan.py --tickets <epic> --write` wrote `STACK_PLAN.md` and `.json`; `--default-estimate 42` applies only where `**Estimate:**` is absent. |
| B12 Companion gates | pass | workflow-harness: ADR strict 3 decisions, canary 2 workflows, ticket order 3 tickets registry last, retro wrote `RETRO_RUNS.md`; 212 tests green. |

## Notes

- No UI or HTTP surface is involved; all clauses are CLI or artifact behavior.
- The retro fixture lives under `/tmp`; the ship tree is unchanged by B7.
- B2 is N/A on this epic because no prototype was recorded; the failure path is
  proved by a fixture, which is the behavior the gate adds.
- The workflow-harness tree is a separate repo and its CI is authoritative; the
  local run is recorded here for the companion clause only.

## Verdict

All 12 clauses pass. No blocked or failing clause.
NEXT_SKILL=/pr_review
