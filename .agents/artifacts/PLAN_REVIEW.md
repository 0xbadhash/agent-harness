# PLAN-REVIEW — markdown escape-hatch audit

**Marker:** PLAN-REVIEW
**Plan:** `.agents/specs/2026-11-27-markdown-escape-hatch-audit-plan.md`
**Reviewer:** self-review against the spec and the live gate pack

## Findings

- The plan extends two existing checkers instead of adding a second gate pack.
  Approve.
- The baseline ratchet keeps the whole-tree audit from failing on legacy comments
  while still blocking new prose. Approve.
- The Markdown scanner reads the harness `skills/` tree first, so installed copies
  cannot create duplicate findings. Approve.
- The DEBUG-tag check makes the existing `diagnosing-bugs` promise true instead of
  deleting the promise. Approve.
- Three implementation steps, so no ticket directory is needed.

## Verdict

Approve. The approach is the smallest change that makes the escape-hatch rule
deterministic, with a baseline rollback path.
