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
