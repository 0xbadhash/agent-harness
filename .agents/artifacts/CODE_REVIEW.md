# CODE-REVIEW — night shift no kanban.md write (1.4.36)
**Marker:** CODE-REVIEW  
**Verdict:** PASS / approve  

## Findings
- No P0: `write_vault` no longer calls kanban sync; upsert/sync are no-ops that never write or create `agent-tasks/kanban.md`.
- `KANBAN_AUTO_MARKER` removed; docstring updated.
- Tests assert no-op + no file mutation/creation via `write_vault`.
- Out of scope leftovers (ops_dashboard, night reports) intentionally unstaged.
- Does not reopen 1.4.35 trait gates. Night-bar 73c2221 not on branch.

## Verdict
Approve merge/tag of v1.4.36.
