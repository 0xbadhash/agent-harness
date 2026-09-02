# Agent-config gates: stale refs, edit guard, green checkpoint, evals

- **Product:** agent-harness
- **Created:** 2026-09-02
- **Status:** ready-for-agent
- **Priority:** P1
- **Roadmap:** CHANGELOG.md
- **Plan:** none
- **Tracker:** local
- **Constitution:** policy defaults
- **Grill-me:** complete

## Problem Statement

Agent instructions rot, session edits can rewrite tests/secrets, ships keep looping after green, and skill/`AGENTS` changes are not regression-tested.

## Solution

Fail-closed scripts re-read from disk: stale-ref check, edit guard on diffs, green SHA checkpoint that stops extra `next_skill` loops, frozen agent-config evals in CI.

## User Stories

1. As a ship operator, I want missing script/skill names in agent config to fail hard_gates.
2. As a reviewer, I want `.env` / secrets and fix-task test rewrites blocked on the diff.
3. As an agent, after score ≥95 at this SHA I must go to `/release_mgmt`, not another polish loop.
4. As CI, I run frozen evals when agent-config gates change.

## Implementation Decisions

- No Claude Code hooks / CLAUDE.md / coordinator / intent.md home.
- No product VERSION bumps on portfolio install.

## Testing Decisions

- unittest for each gate + `run_agent_config_evals.py`
- product smoke

## Acceptance Criteria

- [ ] `check_stale_agent_config.py` fails on missing `scripts/*.py` in AGENTS.md
- [ ] `check_edit_guard.py` fails on `.env` in diff and on test rewrites in `--fix-task`
- [ ] `next_skill` after code_review at green HEAD → `/release_mgmt`
- [ ] `run_agent_config_evals.py` exit 0 on harness SoT
- [ ] Product smoke green; origin `v$VERSION` matches HEAD
- [ ] Portfolio install `--force --push` without product VERSION bumps

## Out of Scope

- Non-engineer intent.md
- Named coordinator
- Headless prod→ship
- Compaction triage engine
- Reopen 1.4.35–1.4.38 PASSes as product work

## Grill-me

**Status:** complete
**Date:** 2026-09-02

### G1 Outcome
- Q: Done sentence?
  - A: Operator: implement ranked gaps 1–4 then full ship FSM + product install.
  - Recommended was: stale refs + edit guard + green checkpoint + evals + portfolio.

### G2 Non-goal / kill
- Q: What not to build?
  - A: (default) No coordinator, no intent.md Cowork path, no auto-ship from night.
  - Recommended was: that default.

### G3 Wrong product
- Q: Wrong repo?
  - A: agent-harness SoT only; products get install, no product VERSION bump.

### G4 Cheapest alternative
- Q: Smallest ship?
  - A: Four scripts + hard_gates/next_skill/CI; no Claude API evals.

### G5 Abuse / failure
- Q: Failure mode?
  - A: Fail closed; do not weaken tests on a fix; secrets paths blocked.

### G6 Verify
- Q: Proof?
  - A: unittests + evals + smoke + finish_ship --require-push.

### G7 Priority
- Q: Why now?
  - A: Operator ordered 1–4 now.

## Clarifications

### 2026-09-02
- Q: Order 1–4 only?
  - A: Yes. Full FSM then all products.

## Handoff

- Next: `/execute_dev` (this session implements)
