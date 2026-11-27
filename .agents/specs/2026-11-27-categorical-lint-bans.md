# Categorical lint bans and typed suppressions

- **Product:** agent-harness
- **Created:** 2026-11-27
- **Status:** ready-for-agent
- **Priority:** P1
- **Roadmap:** CHANGELOG.md → Open work
- **Plan:** `.agents/specs/2026-11-27-categorical-lint-bans-plan.md`
- **Tracker:** local
- **Constitution:** `.agents/policy/base_constraints.md` + workspace `AGENTS.md`
- **Grill-me:** complete

## Problem Statement

`ruff.toml` selected only `E`, `F`, and `W`, so blind exceptions, mutable
defaults, `shell=True`, and runaway complexity passed the local gate. The tree
also carried 95 `# type:` suppressions with no owner or expiry, and the raw
`ruff check` in `compliance_engine.py` would fail as soon as new families were
enabled.

## Solution

Enable bugbear, blind-except, `S602`, and mccabe at a threshold of 20, keep the
ratchet as the pass/fail signal, and ban blanket type suppressions outright: every
suppression names an error code, an owner, and a future expiry. The 87 blanket
suppressions that mypy did not need are removed; the eight real errors get typed
fixes.

## Implementation Decisions

- `ruff.toml` selects `["E", "F", "W", "B", "BLE", "S602", "C90"]` with
  `[lint.mccabe] max-complexity = 20`; `E501`/`E402` stay ignored.
- `config/lint_ratchet_baseline.json` records `B904=1`, `B905=2`, `BLE001=44`,
  `C901=14`; new occurrences fail, declines are welcome.
- `compliance_engine.py` runs `scripts/check_lint_ratchet.py` when present, with
  raw ruff as the product fallback.
- New `scripts/check_type_ignores.py` fails blanket, unowned, and expired
  suppressions; the live tree has none.
- `hard_gates` and `validate.py` run the suppression check.
- Non-goals: auto-fixing the 44 blind excepts, changing the TODO warning, or
  enabling every bandit rule.

## Testing Decisions

- `tests/test_lint_config.py` pins the selected families and the complexity
  threshold.
- `tests/test_type_ignores.py` covers blanket, missing owner, expired, annotated,
  skip dirs, and the live tree.
- `tests/test_hard_gates.py` asserts the `type_ignores` violation.
- `mypy scripts tests` must stay clean without suppressions.
- Commands: targeted pytest, full pytest, `product_smoke.py`, `validate.py full`.

## Acceptance Criteria

- [ ] AC-1: `ruff.toml` selects `B`, `BLE`, `S602`, `C90` and sets
  `max-complexity = 20`; `tests/test_lint_config.py` passes.
- [ ] AC-2: `check_lint_ratchet.py` passes at the recorded counts and exits 1 when
  a rule count rises.
- [ ] AC-3: `check_type_ignores` fails a blanket suppression, a missing
  owner/expiry, and an expired date; an annotated suppression passes.
- [ ] AC-4: the live tree has zero `# type:` suppressions; `mypy scripts tests`
  reports success.
- [ ] AC-5: `hard_gates` reports `type_ignores`; prose-only ships skip it.
- [ ] AC-6: `validate.py full` passes 9/9 with the compatibility linter using the
  ratchet.
- [ ] AC-7: full suite, smoke, and validate pass; no secrets in the diff.

## Out of Scope

- Burning down the 44 `BLE001` and 14 `C901` findings; the ratchet freezes them.
- Enabling `S` or `PL` as whole families.
- Changing the ownerless-TODO warning policy.

## Grill-me

**Status:** complete
**Date:** 2026-11-27

### G1 Outcome
- Q: What changes for the operator?
  - A: A new blind except, complex function, or blanket suppression fails the
    local gate; existing counts are frozen.

### G2 Non-goal / kill
- Q: Is this a mass auto-fix?
  - A: No. Suppressions are removed because mypy does not need them; rule findings
    are ratcheted, not rewritten.

### G3 Wrong product
- Q: Could this block a product with its own ruff config?
  - A: The ratchet reads `config/lint_ratchet_baseline.json`; a product without it
    sees an empty floor and fails only on new findings in the selected families.

### G4 Cheapest alternative
- Q: Could a review note cover this?
  - A: No. The video's point is that a category must be eliminated in code, and
    the ratchet plus suppression ban does that.

### G5 Rollback
- Q: How do we undo it?
  - A: Restore `E,F,W` in `ruff.toml` and delete the `type_ignores` calls; the
    suppression removals are behavior-neutral annotation fixes.
