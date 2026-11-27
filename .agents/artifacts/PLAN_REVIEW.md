# PLAN-REVIEW — correction → check wiring

**Marker:** PLAN-REVIEW
**Plan:** `.agents/specs/2026-11-27-correction-checks-plan.md`
**Reviewer:** self-review against the spec and the live gate pack

## Findings

- The plan reuses existing checkers and their helpers; it does not fork gate logic. Approve.
- The `(ok, messages)` contract matches the 15 existing gate modules, so `hard_gates` integration stays uniform. Approve.
- Diff-scoped comment auditing avoids blocking unrelated ships on pre-existing comments. Approve.
- The compatibility risk (older `CODE_REVIEW.md`) is named with the exact remediation in the failure message. Approve.
- One follow-up, not a blocker: if a fourth whole-tree check is added, extract the repeated guarded-call pattern.

## Verdict

Approve. The approach is the smallest change that makes the correction
deterministic in the local review pack, with a clear rollback.
