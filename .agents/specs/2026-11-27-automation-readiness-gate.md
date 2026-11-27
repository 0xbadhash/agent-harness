# Automation readiness gate before the outer loop

- **Product:** agent-harness
- **Created:** 2026-11-27
- **Status:** ready-for-agent
- **Priority:** P1
- **Roadmap:** CHANGELOG.md → Open work
- **Plan:** `.agents/specs/2026-11-27-automation-readiness-gate-plan.md`
- **Tracker:** local
- **Constitution:** `.agents/policy/base_constraints.md` + workspace `AGENTS.md`
- **Grill-me:** complete

## Problem Statement

The bounded outer loop (night-shift autofix) repairs whatever a failing gate
leaves behind, so it can run on a repo whose inner loop is already broken in
ways the fixers cannot see: an expired suppression, an unmapped correction, a
stale behavior report, or a coverage artifact from an older commit. A fix run
on that base produces noise, hides the real defect, and can mask a failing
gate by reformatting around it.

## Solution

Add `scripts/check_automation_ready.py`, a fail-closed gate that proves the
inner loop before automation may act:

- the lint ratchet, suppression ban, and correction map pass;
- `.agents/artifacts/BEHAVIOR_REPORT.md` carries its marker and `NEXT_SKILL=`;
- `.agents/artifacts/coverage.json` is fresh (24h cap);
- a named owner exists (`--owner`, `AUTOMATION_OWNER`, or `**Owner:**` in
  `PR_DRAFT.md`).

`--write` records `.agents/artifacts/AUTOMATION_READINESS.md` with an
`AUTOMATION-READY` marker and the evidence rows. `attempt_autofix` gains
`require_readiness`; when set it returns an `autofix_blocked` record and touches
nothing unless the artifact passes. `night_shift_readiness.py` sets it from
`night_shift.require_automation_ready` or `AUTOFIX_REQUIRE_READY=1`.

## Implementation Decisions

- The gate is a sibling script, not part of `hard_gates`, so a PR diff does not
  depend on artifact freshness.
- The artifact is the cheap per-run signal; `--require-artifact` validates it
  without re-running the probes.
- Default is off for products; the harness opts in through its plugin.
- Staleness is 24h so an artifact from the previous green run still counts at
  the next nightly start.
- Non-goals: auto-refreshing the artifact from `validate.py`, and gating the PR
  validator on it.

## Testing Decisions

- `tests/test_automation_ready.py` covers a clean pass, missing owner, owner from
  `PR_DRAFT.md`, stale coverage, missing behavior report, failed lint, artifact
  roundtrip/freshness/failure recording, and autofix refusal with and without
  the gate.
- The live run must pass with `--owner 0xbadhash` and write the artifact.
- Commands: targeted pytest, full pytest, `product_smoke.py`, `validate.py full`.

## Acceptance Criteria

- [ ] AC-1: `check_automation_ready.check` fails when any precondition fails and
  names each failed row.
- [ ] AC-2: `--write` records `AUTOMATION_READINESS.md`; `--require-artifact`
  rejects a missing, stale, or failed artifact.
- [ ] AC-3: `attempt_autofix(require_readiness=True)` returns `autofix_blocked`
  and runs no fixer without a current artifact.
- [ ] AC-4: `night_shift_readiness.py` passes the flag from the plugin or env.
- [ ] AC-5: harness plugin opts in; docs describe the refresh command.
- [ ] AC-6: full suite, smoke, and validate pass; no secrets in the diff.

## Out of Scope

- Gating `/pr_review` or `/release_mgmt` on artifact freshness.
- Auto-generating the artifact from a successful `validate.py full`.
- Changing the bounded fixer set.

## Grill-me

**Status:** complete
**Date:** 2026-11-27

### G1 Outcome
- Q: What changes for the operator?
  - A: The outer loop refuses to act on an unproven base and logs `autofix_blocked`;
    a green inner loop records the artifact with one command.

### G2 Non-goal / kill
- Q: Is this a new autofixer?
  - A: No. It gates the existing bounded fixers.

### G3 Wrong product
- Q: Does every product need the artifact?
  - A: No. The flag defaults off; the harness opts in as the reference proof.

### G4 Cheapest alternative
- Q: Could a review note cover this?
  - A: No. The failure mode is behavior at 3am, so the check must run in code.

### G5 Rollback
- Q: How do we undo it?
  - A: Set `require_automation_ready: "0"` or unset `AUTOFIX_REQUIRE_READY`;
    the script and artifact are inert otherwise.
