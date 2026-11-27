# 03 — Add the workflow-harness glossary and ticket fields

**What to build:** `workflow-harness/glossary.json` defines the ingest domain
terms, and both tickets declare blocking edges, status, and checkable acceptance.

**Blocked by:** 02

**Status:** ready-for-agent

- [ ] `glossary.json` parses as JSON, has a version, and defines at least six ingest terms with non-empty definitions.
- [ ] `tickets/02-ingest-fanout.md` has `**Blocked by:**`, `**Status:**`, and at least three acceptance checkboxes.
- [ ] `tickets/01-run-record.md` uses the same field shape so the ticket DAG parses both.
- [ ] The workflow-harness test suite validates the glossary and ticket fields.
