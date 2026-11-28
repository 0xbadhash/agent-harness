# PLAN-REVIEW — close the remaining top-50 gaps

**Marker:** PLAN-REVIEW
**Plan:** `.agents/specs/2026-11-28-top50-gap-closure-plan.md`

## Coverage

- AC-1 and AC-4 (glossary data) map to `docs/glossary.md`, the standalone
  `check_glossary.py`, and the two existing path lists. The gate skips when the
  file is absent, so installing the harness in a product does not fail it.
- AC-2 and AC-3 map to `check_comment_audit.py --classify` and `--constraints`.
  The constraint rule is opt-in; the plan explains why a hard gate would fail
  existing source.
- AC-4 and AC-5 map to the ticket template and `run_tickets.record_session`.
  The plan also fixes `_ids` so `None — can start immediately` is no longer read
  as five dependency ids.
- AC-6 maps to the detached re-exec. A unit test covers the argv builder and a
  dry run covers the unchanged path.
- AC-7 maps to the prototype field and the import scan.
- AC-8 maps to `tools/weekly_retro.py` and the scheduled workflow.

## Findings

- **P1 (accepted):** the ticket DAG parser treats the template's
  `None — can start immediately` as dependency ids. Without a fix the new
  tickets have no ready frontier. Folded into ticket 03.
- **P2 (accepted):** `--constraints` will flag many existing comments. The plan
  keeps it opt-in and names the waiver; no hard-gate change.
- **P2 (rejected):** run the merge in a supervised daemon. A detached process
  with a log is enough for one merge command and avoids a second state model.

## Verdict

**Approve.** The plan is additive, each acceptance criterion has a command, and
the two accepted findings are inside the ticket boundaries. No reserved
decision is taken without the operator.
