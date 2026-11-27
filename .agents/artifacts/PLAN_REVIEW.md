# PLAN-REVIEW — categorical lint bans

**Marker:** PLAN-REVIEW
**Plan:** `.agents/specs/2026-11-27-categorical-lint-bans-plan.md`
**Reviewer:** self-review against the spec and the live gate pack

## Findings

- Enabling families with a ratchet avoids a 60-finding cleanup blocking the ship.
  Approve.
- Using the ratchet in `compliance_engine.py` keeps `validate.py full` and CI on
  one lint signal. Approve.
- Removing suppressions that mypy does not need is behavior-neutral and shrinks
  the suppression surface to zero. Approve.
- The eight real errors get typed fixes (`Any` for `fcntl`, `Callable | None`,
  `cast`) instead of new blanket suppressions. Approve.
- The suppression ban is absolute because the tree is already at zero; no second
  baseline is needed.

## Verdict

Approve. The change eliminates a category in configuration and code, with a named
rollback.
