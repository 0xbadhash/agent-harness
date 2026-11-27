# Correction → check: wire ratchet and comment audit into hard gates

- **Product:** agent-harness
- **Created:** 2026-11-27
- **Status:** ready-for-agent
- **Priority:** P1
- **Roadmap:** CHANGELOG.md → Open work
- **Plan:** `.agents/specs/2026-11-27-correction-checks-plan.md`
- **Tracker:** local
- **Constitution:** `.agents/policy/base_constraints.md` + `AGENTS.md` (workspace)
- **Grill-me:** complete

## Problem Statement

Corrections to the agent still land as prose in review notes. The harness already
owns a lint ratchet and a comment audit, but neither runs inside the local
fail-closed pack: `check_lint_ratchet.py` runs only in daytime CI, and
`check_comment_audit.py` runs only in unit tests. A ship can therefore pass
`/pr_review --validate` with a lint regression, a new history/dead-code comment,
or no recorded link from an accepted finding to a check.

## Solution

`/pr_review --validate` fails locally when the lint ratchet regresses, when the
diff adds a history/commented-code/ownerless-TODO comment, or when the closeout
review has no correction → check map. Each accepted review finding must name the
deterministic check that prevents recurrence, or an explicit signed `no-check`
reason.

## User Stories

1. As the harness operator, I want a lint regression to fail `hard_gates`, so that the ratchet is not bypassed by skipping CI.
2. As a reviewer, I want a new history comment to fail `hard_gates`, so that the same correction is enforced in code.
3. As a reviewer, I want every accepted finding mapped to a check or a signed no-check reason, so that review prose cannot silently replace a gate.

## Implementation Decisions

- Add `check(root)` to `scripts/check_lint_ratchet.py`, returning `(ok, messages)` and reusing `load_baseline` / `run_ruff` / `compare`.
- Add `check(root, base, head)` to `scripts/check_comment_audit.py`, auditing added diff lines (whole-tree mode stays available from the CLI).
- Add `scripts/check_correction_checks.py` with `check(root)`, validating `.agents/artifacts/CODE_REVIEW.md`:
  - requires a `## Correction checks` section;
  - every bullet must map a finding to a check (`→ tests/...`, `→ ruff ...`, `→ gate ...`) or to `no-check: <reason>` (reason ≥ 10 chars);
  - a bullet containing `none` is accepted for a review with no findings.
- Call all three from `scripts/hard_gates.py` for non-prose ships. Missing `ruff` fails closed with an actionable message.
- Document the rule and the artifact section in `skills/code_review/SKILL.md`.
- Non-goals: enabling new ruff rule families, cleaning pre-existing comments, changing CI wiring.

## Testing Decisions

- Unit-test each `check()` with temporary trees: over-baseline counts fail; at-baseline counts pass; history comments on added lines fail while pre-existing ones pass; correction map missing/malformed fails and well-formed passes.
- Integration-test `hard_gates.evaluate` by patching the three checkers to fail, asserting the `hard_gates: <name>` violations appear for code ships and are skipped for prose-only.
- Commands: `python3 -m pytest tests/test_hard_gates.py tests/test_correction_checks.py tests/test_comment_audit.py tests/test_lint_ratchet.py -q`, then `bash scripts/smoke_unit.sh`.

## Acceptance Criteria

- [ ] AC-1: `check_lint_ratchet.check(root)` returns `(False, …)` when a rule count exceeds the baseline and `(True, …)` when all counts are at or below it.
- [ ] AC-2: `check_comment_audit.check(root, base, head)` fails on a history comment added by the diff and ignores the same comment when it pre-exists the range.
- [ ] AC-3: `check_correction_checks.check(root)` fails when `CODE_REVIEW.md` lacks `## Correction checks`, and passes with either `- finding → tests/test_x.py` or `- finding → no-check: <reason ≥10 chars>`.
- [ ] AC-4: `hard_gates.evaluate` adds `hard_gates: lint_ratchet`, `hard_gates: comment_audit`, and `hard_gates: correction_checks` violations when the matching checker fails; prose-only ships skip all three.
- [ ] AC-5: `skills/code_review/SKILL.md` documents the correction → check rule and the `## Correction checks` report section.
- [ ] AC-6: new and updated unit tests pass.
- [ ] AC-7: `bash scripts/smoke_unit.sh` passes.
- [ ] AC-8: No secrets committed.

## Out of Scope

- Enabling bugbear/complexity ruff families (separate enhancement).
- Cleaning existing history comments across the tree.
- Changing `.github/workflows/daytime-gates.yml`.
- Running the new checks for prose-only ships.

## Grill-me

**Status:** complete
**Date:** 2026-11-27

### G1 Outcome
- Q: What changes for the operator?
  - A: A local `/pr_review --validate` fails on lint regressions, new history/dead-code comments, and reviews without a correction → check map.

### G2 Non-goal / kill
- Q: Is this a whole-tree cleanup?
  - A: No. It prevents new occurrences; existing findings stay out of scope.

### G3 Wrong product
- Q: Could this block legitimate ships?
  - A: Only when a checker fails. Each failure message names the fix, and `no-check: <reason>` is the documented escape hatch for findings that cannot be checked.

### G4 Cheapest alternative
- Q: Why not leave the ratchet in CI?
  - A: The review pack is the ship's fail-closed gate; CI is skipped locally and on some hosts.

### G5 Abuse / failure
- Q: What if `ruff` is absent?
  - A: Fail closed with an install/`--report` message; the repo ships ruff in `.venv` and on PATH.

### G6 Verify
- Q: How is it proven?
  - A: Unit tests per checker plus a `hard_gates` integration test; `smoke_unit.sh`.

### G7 Priority
- Q: Why first?
  - A: Cheapest item: both checks already exist; this only wires them.

## Clarifications

### 2026-11-27
- Q: Scope and ship boundary?
  - A: Operator selected agent-harness items 1–5 in order and approved the full FSM including push to `main` and tags.

## Further Notes

- Products with an older `CODE_REVIEW.md` will need the `## Correction checks` section after upgrading the harness. The failure message states the exact heading to add.
- The comment audit stays diff-scoped inside `hard_gates` so pre-existing tree findings do not block unrelated ships.

## Handoff

- Next: `/execute_dev` (TDD: add failing tests first)
- Then: `/code_review` → `/pr_review --validate` → `/release_mgmt` → `/sync_docs`
