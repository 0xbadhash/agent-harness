---
name: handoff
description: >
  Write a clipboard-ready handoff prompt for another agent to continue or
  investigate a task (independent review first). Not a ship FSM step.
disable-model-invocation: true
user-invocable: true
max-retries: 0
timeout-seconds: 300
---

# `/handoff` — multi-agent continuity (P2)

Use when: switching agents/sessions, blocked, or user says “handoff / delegate”.

## Workflow

1. Identify task from user text + repo context (branch, kanban card, recent commits).
2. Gather starting context only — do **not** decide the full technical solution for the receiver.
3. Write a **standalone** prompt for a **fresh** agent that:
   - Starts a discussion / investigation, not a blind work order
   - Requires **independent review** before edits
   - Asks whether the task is still valid, stale, over-scoped, or better done differently
   - Lists product path, constraints, known symptoms, links to specs/kanban
   - Points at ship path: `python3 scripts/next_skill.py --after execute_dev` after they implement
4. Save to `.agents/artifacts/HANDOFF.md` and/or copy to clipboard if available.
5. Final user reply: short confirmation + path to handoff file. Paste full prompt only if asked.

## Do not

- Advance pipeline phases
- Invent secrets or host topology
- Command the receiver to skip `/code_review` on code ships

## Handoff

```text
NEXT_SKILL=(continue with task)
```
