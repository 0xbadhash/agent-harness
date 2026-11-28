# 03 — Ticket fields and session recording

**What to build:** the ticket template fields the DAG gate expects, plus writing the runner session id back to the ticket.

**Kind:** feature
**Prefactor:** none
**Touches:** skills/spec/references/spec-template.md, scripts/check_ticket_dag.py, scripts/run_tickets.py
**Blocked by:** None — can start immediately
**Status:** done

- [x] The ticket template carries Kind, Prefactor, Touches, and Session.
- [x] `check_ticket_dag` reads Touches and still fails a shared-component ticket without a prefactor.
- [x] `run_tickets.py` writes `**Session:** <id>` after a successful real run and leaves the file alone on a dry run.
