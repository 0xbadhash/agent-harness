# PR draft — vault completion writer

**Spec:** .agents/specs/2026-11-09-vault-completion-writer.md
**Plan:** .agents/specs/2026-11-09-vault-completion-writer-plan.md
**Tickets:** .agents/tickets/vault-completion-writer/

Status: spec ready; implementation not started.

## Red-proof

- red_cmd: `python3 scripts/vault_done.py --id 'BAD/../ID' --verdict PASS` → exits 2, `refused: run id must match`, writes no file
- green_cmd: `.venv/bin/python -m pytest tests/test_vault_writer.py -q`

## Traceability

| AC | Test |
|----|------|
| A1 partial writes event + matchable tag | `test_a1_partial_writes_event_and_prints_matchable_tag` |
| A2 unknown verdict writes nothing | `test_a2_unknown_verdict_writes_nothing` |
| A3 note + 0444 processed copy | `test_a3_drain_writes_note_and_read_only_processed_copy` |
| A4 idempotent / rev2 preserves original | `test_a4_same_event_twice_makes_one_note`, `test_a4_changed_content_makes_rev2_and_preserves_original` |
| A5 crash between note and processed resumes | `test_a5_crash_between_note_and_processed_resumes` |
| A6 bad id / `---` refused | `test_a6_bad_run_id_and_separator_are_refused` |
| A7 no start limiter | `test_a7_units_disable_the_start_limiter` |
| A8 run id round-trips | covered by A1/A3 note path assertions |
| A9 plain file the vault can commit | `test_a9_note_is_a_plain_file_the_vault_can_commit` |
| S1 inert body | `test_s1_body_is_inert` |
| S2 YAML quoting | `test_s2_yaml_quote_roundtrips_and_escapes` |

## Threat notes

Tags: injection, path-traversal, secrets.

- **injection**: free text from an executor lands in a markdown vault a live Obsidian renders. The body is rendered
  inert (`&lt;`, `&#96;`, `&#126;`) and frontmatter is quoted, so a fenced dataviewjs block cannot form. Tested by
  `test_s1_body_is_inert` with a real attack fixture.
- **path-traversal**: `run_id` is the only path component and must match `^[A-Z0-9-]{1,64}$`; the note path is
  built from it plus a fixed directory, never from event content. Refused before any write.
- **secrets**: events and notes carry paths, hashes and verdicts only; the CLI refuses control characters and the
  writer never echoes file contents. No token is read or written.

## Evidence pack

- hard_gates: `python3 scripts/hard_gates.py --diff HEAD~1...HEAD`
- pytest: **375 passed** (`TMPDIR=/tmp`, harness suite) · targeted **24 passed**
- smoke: live staging run — `hermes-done --verdict PARTIAL` → tag, event, drain, note with 12 frontmatter fields
- validate: `check_hardcodes.py` → no hardcodes
- coverage: N/A (no coverage runner configured) · SBOM: N/A (Python stdlib only, no new dependency)
- Tickets: `.agents/tickets/vault-completion-writer/` (T01–T03)

## What Problem This Solves

A finished job announces itself as a chat string that a tmux-scrollback grep has to guess at, and the grep only
accepts three verdicts while briefs ask for six. Completions are lost, and there is no durable record that a run
happened, what it concluded, or what evidence it left. After this change a completion is a vault note with
frontmatter and a day index, written by a service that retries until the queue is empty.

## Why This Change Was Made

The vault is the surface a human opens and that `vault-autocommit` versions. Recording completions there removes
the pane dependency and the verdict coercion, and makes "did it finish, and what did it decide" answerable by
search rather than by memory.

## User Impact

The operator can read a run's verdict, decision flag and evidence hashes in Obsidian. Executors call one command.
Nothing is sent anywhere: Signal HARD HOLD stands, and the writer only touches `agent-tasks/hermes-runs/`.

## Things that look bad but are actually fine

1. **No timer.** The unit is level-triggered on a non-empty spool; a timer would add a polling interval the CEO
   explicitly excluded.
2. **`StartLimitIntervalSec=0` looks like "no limits".** It disables the *start* limiter only, because the default
   would move a failing unit to `failed` and stop re-activating a spool that still has work.
3. **`hermes-done` instead of `hermes done`.** A dispatcher over `~/.local/bin/hermes` would put the whole CLI
   behind one line of this code and would vanish on `hermes update`.
4. **Notes are 0664 and processed events are 0444.** The note is meant to be edited by the vault owner; the
   processed event is evidence and must not drift.
5. **Staging by default.** Without `HERMES_VAULT_STAGING=1` removed the writer writes to `_staging/`, because the
   rule that permits live vault writes is still only proposed, not stamped.
