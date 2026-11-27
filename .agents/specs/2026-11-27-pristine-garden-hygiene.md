# Pristine garden: scratch artifacts and dirty tree fail the pack

- **Product:** agent-harness
- **Created:** 2026-11-27
- **Status:** ready-for-agent
- **Priority:** P1
- **Roadmap:** CHANGELOG.md → Open work
- **Plan:** `.agents/specs/2026-11-27-pristine-garden-hygiene-plan.md`
- **Tracker:** local
- **Constitution:** `.agents/policy/base_constraints.md` + workspace `AGENTS.md`
- **Grill-me:** complete

## Problem Statement

The harness asks products for a clean tree, yet its own tree carried backup files, a
coverage database, and uncommitted cross-window edits. `check_repo_hygiene.py` only
looks for `MagicMock` imports and orphan TODOs, so scratch files pass the gate. Agents
copy what looks established, including a `.bak` sibling.

## Solution

`check_repo_hygiene` fails on backup/scratch artifacts and, when asked, on a dirty git
tree. `hard_gates` calls it with the clean requirement so `/pr_review --validate`
cannot pass from a tree that still holds scratch state.

## Implementation Decisions

- Add `scan_scratch_artifacts(root)` covering `*.bak-*`, `*.orig`, `*.rej`, `.coverage`,
  `.coverage.*`, `.venv-*bak*`, `signal-cli-canary-*`, skipping `.git`, `.venv`,
  `.agents`, `node_modules`, `__pycache__`.
- Add `check(root, require_clean=False)` returning `(ok, messages)` with `fail:` and
  `warn:` prefixes, matching the gate contract.
- `require_clean=True` runs `git status --porcelain`; a non-repo root is a warning, not
  a failure, so product fixtures keep working.
- Wire the checker into `hard_gates` for non-prose ships.
- Add the patterns to `.gitignore`; remove the existing `night_shift_runtime.yaml.bak-t1659u`.
- Non-goals: deleting unrelated untracked scripts, changing the TODO warning policy.

## Testing Decisions

- Unit tests create temp trees with each scratch pattern and assert failure; a clean tree passes.
- Dirty-tree test initializes a temp git repo, adds an uncommitted file, asserts failure;
  commits it and asserts pass.
- A hard_gates test patches the checker to fail and asserts the `repo_hygiene` violation.
- Commands: targeted pytest, full pytest, `product_smoke.py`, `validate.py full`.

## Acceptance Criteria

- [ ] AC-1: `check(root)` fails for each of `x.bak-1`, `x.orig`, `x.rej`, `.coverage`, `.venv-oldbak`, `signal-cli-canary-1`.
- [ ] AC-2: `check(root, require_clean=True)` fails on a dirty temp repo and passes after commit.
- [ ] AC-3: `hard_gates.evaluate` reports `hard_gates: repo_hygiene` when the checker fails; prose-only ships skip it.
- [ ] AC-4: `.gitignore` lists the backup/scratch patterns and the tree no longer contains a `.bak-*` file.
- [ ] AC-5: new unit/integration tests pass; full suite stays green.
- [ ] AC-6: product smoke and `validate.py full` pass.
- [ ] AC-7: No secrets committed.

## Out of Scope

- Removing `bin/restore_product_venvs.sh` (a restore tool, locally excluded).
- Making the TODO warning a failure.
- Cleaning other repositories.

## Grill-me

**Status:** complete
**Date:** 2026-11-27

### G1 Outcome
- Q: What changes for the operator?
  - A: `/pr_review --validate` fails when the tree holds a backup or uncommitted file.

### G2 Non-goal / kill
- Q: Is this a repo-wide cleanup?
  - A: No. It prevents new scratch state and removes the one live `.bak`.

### G3 Wrong product
- Q: Could this block legitimate ships?
  - A: Only when scratch files or uncommitted changes exist; the message names them.

### G4 Cheapest alternative
- Q: Why not a review checklist item?
  - A: Check lists are prose; the talk's rule is to make corrections deterministic.

### G5 Abuse / failure
- Q: What about product fixtures with backup-like filenames?
  - A: Tests live under temp dirs; `tests/` fixtures are not exempt because the gate is opt-in per ship and `hard_gates` runs at review time.

### G6 Verify
- Q: How is it proven?
  - A: Per-pattern unit tests, a real temp git repo for the dirty case, and a hard_gates integration test.

### G7 Priority
- Q: Why second?
  - A: The live tree had 12 dirty entries and two backup classes; it is cheap and recurring.

## Clarifications

### 2026-11-27
- Q: Scope and ship boundary?
  - A: Operator selected agent-harness items 1–5 and approved the full FSM including push and tags.

## Further Notes

- `git status --porcelain` honors `.gitignore`, so locally excluded tools do not fail the gate.
- The checker is filesystem-based for scratch patterns; it sees a `.bak` even if ignored, which is intentional.

## Handoff

- Next: `/execute_dev` (TDD)
- Then: `/code_review` → `/pr_review --validate` → `/release_mgmt` → `/sync_docs`
