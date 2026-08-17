# Spec: Slim portable skill portfolio

- **Product:** agent-harness
- **Created:** 2026-08-15
- **Status:** ready-for-agent
- **Priority:** P1
- **Plan:** none (skill/docs only)
- **Grill-me:** complete

## Problem Statement

Too many portable skills diluted ship_skills; operators and agents overloaded. Outer-loop thin skills (feedback, plan_backend, test_automation, audit_repo) overlapped stronger tools.

## Solution

Remove or demote low-value skills; fold capabilities into `/spec`, `/night_shift`, `/sweep`, `/audit_harness`.

## Acceptance Criteria

- [x] AC-1: `feedback` skill removed + removed_portable list
- [x] AC-2: `agent_transcript` + `session_viewer` demoted (optional_skills, not ship_skills)
- [x] AC-3: `plan_backend` removed; `/spec --roadmap-from-gap` documents merge
- [x] AC-4: `test_automation` removed; night_shift owns suite orchestration section
- [x] AC-5: `audit_repo` removed; sweep primary obsolete; audit_harness policy-gap
- [x] AC-6: ship_skills.txt has 14 required skills; verify_skills green
- [x] AC-7: docs catalog / README / llm-bootstrap / policies updated

## Grill-me

**Status:** complete  
**Date:** 2026-08-15

### G1 Outcome
- Q: Done?
  - A: Slimmer ship_skills; removed skills gone; merges documented.

### G2 Non-goal
- Q: Kill what?
  - A: Do not remove ship core or night_shift/sweep.

### G3 Wrong product
- Q: Repo?
  - A: agent-harness SoT only.

### G4 Cheapest
- Q: Smallest?
  - A: Delete dirs + list updates + doc merges (this PR).

### G5 Abuse
- Q: Break products?
  - A: removed_portable + --delete-stale-skills on reinstall.

### G6 Verify
- Q: Prove?
  - A: verify_skills.py exit 0.

### G7 Priority
- Q: Why now?
  - A: Operator requested after outer-loop review.

## Out of Scope

- Deleting session_viewer / agent_transcript scripts
- Changing grill-me defaults
