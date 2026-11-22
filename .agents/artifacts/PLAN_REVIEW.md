# PLAN-REVIEW

**Marker:** PLAN-REVIEW
**Plan:** `.agents/specs/2026-11-08-ops-dashboard-contract-plan.md`
**Verdict:** PASS

## Findings

No material issues. The plan keeps the running timer as it is.

Product: the user-facing gap is ambiguous unit text, not a new dashboard feature. Commenting the unit and the registry row is the whole slice. Rewriting `ops_dashboard.py` would be the wrong surface.

Security: no new executed path, no secret, no change to who may write the vault. `SuccessExitStatus=0 2` stays so an intentional RED does not become a timer failure.

Ops: rollback is reverting the comment lines. The smoke path is `systemctl show` plus the contract test. Night-shift and the writer are not restarted.

no material issues beyond the pre-existing Group mismatch, which the plan correctly leaves alone.

---

# PLAN-REVIEW — vault completion writer (2026-11-09)

**Marker:** PLAN-REVIEW
**Plan:** `.agents/specs/2026-11-09-vault-completion-writer-plan.md`
**Spec:** `.agents/specs/2026-11-09-vault-completion-writer.md`
**Verdict: REVISE** — the design holds; six things would bite in production, and one of them can execute code.

## Product lens

- **P1 Volume and churn are unbounded.** One note per run plus an append to the day's `INDEX.md` is fine at ten
  jobs a day and corrosive at a hundred. `INDEX.md` is rewritten on every append, and Syncthing plus a live
  Obsidian instance both run against this vault (checked this session), so a busy day becomes a sync hot file.
  Needs a stated volume policy and an index that is rebuilt once per drain rather than appended per event.
- **P2 No note lifecycle.** Nothing says notes are never deleted. State it, or agents will assume someone cleans up.

## Security lens

- **S1 `detail` is an execution surface, not just text.** Free text from an agent lands in a markdown vault that a
  live Obsidian renders with fence-executing plugins. `yaml_safe()` covers frontmatter; the **body** is unguarded,
  so a `detail` containing a dataviewjs fence or raw HTML executes when a human opens the note. The body must be
  rendered with free text escaped (fences neutralised, backticks and `<` encoded).
- **S2 YAML escaping is specified too thinly.** The reject list misses U+2028/U+2029, tabs, leading `-`/`?`/`:`/`#`
  and trailing spaces. Quoted values need quote-aware escaping, not a reject-list. This needs its own test table.

## Ops lens

- **S3 `DirectoryNotEmpty` plus default limits silently stalls the queue.** A repeatedly failing writer trips
  `StartLimitBurst` (5 in 10 s), after which the unit enters failed state and stops being activated. The plan
  called that trip "the alarm"; it is also the moment retries stop. Needs an explicit `StartLimitIntervalSec`
  decision and a named operator drain procedure.
- **S4 The CLI entry point is undefined.** The spec says `hermes done`; the plan builds `scripts/vault_done.py`.
  Nothing says how the command resolves, so each executor would invent its own invocation.
- **S5 `0444` processed events cannot be corrected.** A malformed-but-valid event has no repair path. Name the
  procedure (who, how) instead of discovering it during an incident.

## Accepted as-is

Manufactured terminality (new inode + unlink), resume-not-skip idempotence, staging-first, no timer, processed
retention, and the concrete permissions matrix are all sound and testable.

## Required before /execute_dev

1. Body escaping for free text (S1) plus tests.
2. Quote-aware frontmatter serialiser covering U+2028/U+2029 and leading indicators (S2).
3. `StartLimitIntervalSec` decision + operator drain procedure (S3).
4. The CLI resolution named (S4).
5. Volume policy, index strategy (P1) and the note-lifecycle statement (P2).
6. A repair procedure for a bad processed event (S5).

Verdict stays **REVISE** until those six are in the plan; then re-run this review.

---

# PLAN-REVIEW (re-run) — vault completion writer, after revision

**Marker:** PLAN-REVIEW
**Plan:** `.agents/specs/2026-11-09-vault-completion-writer-plan.md` · 313 lines · revised by Grok 4.7 (high)
**Verdict: PASS** — all six required items are closed with mechanisms, not intentions.

## Verification of the six

| Item | Closed by | Check |
|---|---|---|
| S1 body escaping | Ticket 05 S1 row + fixture: body must contain no `<`, no backtick, no `~~~` line; asserts `&lt;script>`, `&#96;&#96;&#96;dataviewjs`, `~~&#126;dataviewjs` | concrete, byte-level |
| S2 YAML quoting | `yaml_quote()` + `yaml_quote_cases` table; U+2028/U+2029 emitted as `\u2028`/`\u2029`, tabs as `\t`, leading indicators live inside quotes; no YAML package | correct for YAML 1.1 |
| S3 start limit | `StartLimitIntervalSec=0` with burst untouched, plus a named stage-tagged failure line and a `drain-stalled-spool` operator procedure | right: the default would stall a non-empty spool |
| S4 CLI resolution | changed by me (see below) to a **separate `hermes-done`** entry point | safer than the revision |
| P1 volume/index | index rebuilt once per drain, not appended per event; volume policy stated | closes the sync-churn risk |
| P2/S5 lifecycle + repair | notes declared append-only; repair procedure sits beside the revision rule | closed |

## One deviation from the Grok revision, recorded

Grok's plan made `~/.local/bin/hermes` a dispatcher that forwards non-`done` argv to the real CLI. I rejected that
and rewrote the Resolution row: the whole `hermes` command would sit behind a one-line bug, and any `hermes update`
that rewrites that path silently removes the completion writer. The contract is now a separate
`hermes-done` binary; `hermes done` survives only as an optional alias, explicitly not part of the contract.
Everything else in Grok's revision is kept as written.

## Residual risk accepted

`hermes-done` is a second command name an executor must remember. That is a training cost, not a correctness cost,
and it is smaller than putting the CLI behind a dispatcher.

Verdict: **PASS → /execute_dev** (staging only until the vault-rule stamp exists).
