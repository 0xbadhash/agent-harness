# CROSS-REVIEW

**Marker:** CROSS-REVIEW
**Base:** HEAD~1 (`5b848df^`)
**Head:** `5b848df`
**Secrets:** `check_secrets_diff.py --base HEAD~1 --head HEAD` clean

## Verdict

Blockers: 0. Majors: 0. Obsolete Tier A: 0.

## Security Guru

None. The diff adds comments and a test. `ExecStart`, `SuccessExitStatus=0 2`, and the two base `OnCalendar=` lines are unchanged. No new path is executed. No secret is added. `path-traversal` and `secrets` are called out in the threat notes because the unit already names a vault path; this slice does not widen that path.

## Maintainability Expert

None in the unit text. The contract test locks the directive lines, so a later comment edit that drops `SuccessExitStatus` or adds a base calendar fails the suite.

### Obsolete / cleanup (scoped)

Touched paths: `deploy/ops-dashboard.service`, `deploy/ops-dashboard.timer`, `tests/test_ops_dashboard_contract.py`, the spec, and the review drafts.

| Path | Tier | Confidence | Evidence | Action |
|------|------|------------|----------|--------|
| `deploy/ops-dashboard.service` | keep | 0.05 delete | Installed unit and the test both require `SuccessExitStatus=0 2` | keep |
| `deploy/ops-dashboard.timer` | keep | 0.05 delete | Live timer is enabled; base file still has the 01:00 and 12:00 directives | keep |
| `tests/test_ops_dashboard_contract.py` | keep | 0.0 delete | Named by PR_DRAFT traceability for AC-1..AC-4 | keep |

No stub or "TODO remove" comments were added. Whole-repo cruft was not scanned.

## Domain Specialist

None. Exit 2 matches the writer (`return 0 if overall != RED else 2`). The four calendars match `systemctl show` after daemon-reload: 01:00, 12:00, 19:45, and 23:45 UTC. The timer stayed enabled.

Follow-up, not a blocker: repo `Group=debian` still differs from the installed `Group=secondbrain`. Changing it is a behaviour change and was left out.

## §9

1. Overwriting `PR_DRAFT.md` drops the previous IoC narrative from the working file. That narrative remains in git history on the parent commit.
2. File count is 8 because review artifacts were replaced, not because the unit grew a new schedule.
3. systemd prints `Sun,Mon,Tue,Wed,Thu` as `Mon..Thu,Sun`. Same weekday set.

---

# CROSS-REVIEW — vault completion writer (2026-11-09)

**Marker:** CROSS-REVIEW
**Security lens:** the only untrusted input is event content produced by an executor on the same host. It cannot
select a path (`run_id` grammar), cannot break YAML (quoted serializer), and cannot execute in Obsidian (inert
body). The writer's write scope is one directory, enforced by construction: `runs_dir()/day/run_id.md`.
**Ops lens:** level-triggered unit; the start limiter is disabled on purpose so a non-empty spool keeps firing;
`ExecStopPost` is belt only. A stuck spool is visible as a repeating journal line carrying `stage=` and `run_id=`.
**Product lens:** the note is readable, the index is rebuilt rather than appended, and nothing else in the vault is
touched.

Blockers: 0. Majors: 0. Follow-ups: 1 — the CLI has no `--dry-run`, so an executor cannot see the event before it
lands in the spool. Not required by the spec; recorded rather than silently added.

---

# CROSS-REVIEW — security-root-ioc real homes (2026-11-22)

**Marker:** CROSS-REVIEW
**Base:** parent of `6e616ba`
**Head:** `6e616ba` plus the PR draft threat-tag and red-proof fix
**Secrets:** clean on `HEAD~1...HEAD` before this note
**Blockers:** 0

Security: none. A readable parent no longer stands in for an unlistable child home.
Maintainability: none. Discovery is one function and tests inject `multiuser_home`.
Domain: none. No username hardcoded. `--home` remains the override.

### Obsolete / cleanup (scoped)

No Tier A, B, or C. Confidence 0.9. `resolve_home_roots` is referenced by the scanner and its unit test. The `/home` parent stays as the fail-closed required path when no child exists. Keep the unit and the ship-flow sentence.
