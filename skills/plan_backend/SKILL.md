---
name: plan_backend
description: Generate API-first BACKEND_ROADMAP.md from gap analysis.
disable-model-invocation: true
user-invocable: true
max-retries: 0
timeout-seconds: 300
---
# Reads: PRODUCTION_GAP_ANALYSIS.md, ENGINEERING_ASSURANCE.md
# Writes: BACKEND_ROADMAP.md (product only — harness backlog is .agents/BACKLOG.md)
# Anti-patterns: docs/AGENT_REFERENCE.md
When invoked with `/plan_backend`:
1. Pre-condition: PRODUCTION_GAP_ANALYSIS.md exists
2. Prioritize gaps: P0 (critical) → P1 (high) → P2 (medium)
3. For each item, include: title, acceptance criteria, risk level, dependencies
4. Write BACKEND_ROADMAP.md with P0/P1/P2 sections
5. Output: `✅ ROADMAP READY. Run /execute_dev`
