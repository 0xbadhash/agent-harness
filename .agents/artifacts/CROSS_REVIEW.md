# CROSS-REVIEW

**Marker:** CROSS-REVIEW
**Base:** HEAD~1
**Head:** HEAD (ae01b42)
**Blockers:** 0

## Security Guru

No blocker. The retire command does not take a shell string. It unlinks only `night-shift-readiness.service` and `night-shift-readiness.timer`, and only after `night-shift-all.timer` is present in the same directory and the registry still names watchlist. Secrets scan on HEAD~1...HEAD was clean. No auth surface.

## Maintainability Expert

No blocker. One new script, one test module, and a short operator-note edit. The tests call the public plan and apply functions on a temp directory.

### Obsolete / cleanup (scoped)

| Path | Tier | Confidence | Evidence | Action |
|------|------|------------|----------|--------|
| docs/night-shift.md and skills/night_shift/SKILL.md "disable if present" snippet | B | 0.95 | `rg` for `disable --now night-shift-readiness` in the repo returns no matches after this commit | Removed in this diff. Keep the survivor install steps. |
| scripts/retire_duplicate_night_shift_unit.py | keep | 0.2 | New entry point, named by the docs and by tests/test_retire_duplicate_night_shift_unit.py | Do not delete. |
| deploy/night-shift-all.* | keep | 0.1 | Still the installed nightly unit | Out of this delete set. |

No Tier A delete in the touched paths. Whole-repo cruft is a `/sweep`, not this review.

## Domain Specialist

No blocker. Domain hint is a portable harness with no host-only default in the script. Unit directory, products file, and archive directory are arguments. Watchlist stays a registry row, not a special-case runner.

## Follow-ups

- The second-brain vault copy of `docs/night-shift.md` still has the old disable snippet. This ship does not edit the vault.
- The watchlist repo's `AGENTS.md` still names `night-shift-readiness.timer`. Out of scope. The host unit is already gone.

## Things that look bad but are actually fine

1. The diff is large because the new test file and script are both about 137 lines. The behavior is one command.
2. `red_cmd: false` stays in the draft because the historical red command passes once the module exists.
3. Host `SuccessExitStatus=0 1` on night-shift-all looks like a masked failure. It is the survivor's existing policy and this item does not change it.

## Summary

blocker=0 major=0. Scoped obsolete Tier A count: 0.
