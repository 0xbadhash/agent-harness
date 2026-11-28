# CROSS-REVIEW — top-50 gap closure

**Marker:** CROSS-REVIEW
**Scope:** `origin/main...HEAD` (33 files, 1168 insertions, 139 deletions)
**Secrets scan:** `python3 scripts/check_secrets_diff.py --base origin/main --head HEAD`
→ clean
**Blocker count:** 0

## Personas

1. **Security Guru.** The new checks read repository files and never execute
   them. `check_glossary` parses markdown tables; `weekly_retro` reads
   `var/state/*/run.jsonl` as JSON and writes only under `docs/retros/`. The
   retro workflow runs a first-party script on a hosted runner with
   `contents: write`; it installs only PyYAML and commits only when a report
   exists. No new secret or network call.
2. **Maintainability Expert.** Each gap has one deterministic command and one
   test file. The glossary is the single term source for `spec_gate`,
   `check_compact_safety`, and `check_glossary`. The ticket fields match the
   template the skill writes. The old comment-audit API is unchanged, so the
   existing tests and `hard_gates` keep working.
3. **Operator.** `--background` prints the pid and log path and leaves the
   foreground default untouched. `--constraints` is opt-in, so the 110 existing
   constraint comments do not block unrelated work. The retro schedule is
   additive and manual dispatch stays available.

## Obsolete scan

- No superseded path remains: `check_comment_audit.py` keeps its old flags and
  adds new ones; `check_ticket_dag.py` keeps `Kind`/`Prefactor` and adds
  `Touches`.
- `docs/tdd.md` already had a constraint-to-test section; it now names the route
  table and the approval step instead of duplicating them.

## Verdict

No blockers.
