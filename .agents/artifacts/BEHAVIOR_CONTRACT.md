# Behavior contract — harness top-50 completion

**Marker:** BEHAVIOR-CONTRACT
**Surface:** CLI scripts, generated artifacts, and the ship skills. No web UI.
**Method:** each clause is judged by a command or a named test, not by reading
the implementation.

| # | Clause | Pass condition |
|---|--------|----------------|
| B1 | ADR spine | `check_adr.py --root . --strict` exits 0 with the shipped ADR; a fixture missing the tradeoff, an index row, or the Consequences section exits 1 (or reports the error). |
| B2 | Prototype fidelity | A PR with no `**Prototype:**` field passes as N/A; a copied variant or a missing verdict fails with the file named. |
| B3 | Compact grill handoff | `context_pack.py --compact --spec <spec>` writes `GRILL_HANDOFF.md` containing decisions, glossary changes, ADR links, prototype verdict, and open questions. |
| B4 | Comment ratio | `check_comment_audit.py --ratio` reports comment and code counts; `--diff <range> --strict` exits 0 on a clean range. |
| B5 | Rejected docs patterns | `check_docs_patterns.py --root .` exits 0; a doc that teaches `git push origin main` fails and names the file. |
| B6 | Session cost | `session_context.py --record-tokens N --record-context N --record-cost N` writes `SESSION_COST.md`; before recording it reports `unknown`. |
| B7 | Retro ingest | `retro_job.py --transcripts <dir>` reads transcripts, redacts secret-like lines, and labels every cluster with one of the five action classes. |
| B8 | Merge stack | `merge_stack.py --dry-run` prints `would merge <tid>` in layer order; a non-success check stops the run and names the PR. |
| B9 | Ticket runner | `run_tickets.py --dry-run` lists the frontier in layer order; a failed ticket marks its dependents blocked, and `record_runs` appends session ids only on a real run. |
| B10 | Spec gate | `spec_gate.py --strict` exits 0 on the epic spec; a plan without `## Data model`, a reserved/delegated field, or a user-visible flag declaration fails with the field named. |
| B11 | Stack plan | `stack_plan.py --tickets <dir> --write` creates `STACK_PLAN.md` and `.json`; `--default-estimate` changes only tickets that omit `**Estimate:**`. |
| B12 | Companion gates | In workflow-harness, `check_adr.py --strict`, `check_canary.py`, `check_ticket_order.py`, and `retro_runs.py` all exit 0 on that tree. |
