# Agentic workflow (meta harness)

**This directory is not the product.**

| Layer | What it is | Location |
|-------|------------|----------|
| **Product** | CATALYXT watchlist / valuation PHP app | `migration/`, root PHP, `docs/PRODUCT.md`, design docs |
| **Agentic workflow** | Multi-agent pipeline, skills, gates, worksheets | **`.agents/`** (this tree) + `scripts/*` validators |

Agents use this harness to *change* the product. Humans use the product without reading this tree.

## What lives here

| Path | Role |
|------|------|
| `skills/*/SKILL.md` | Invocable agent skills (`/execute_dev`, `/pr_review`, …) |
| `state/pipeline.json` | FSM: init → ready_for_review → approved → shipped |
| `base_constraints.md` | Shared skill constraints (§9, TDD, handoff) |
| `AGENT_WORKFLOW.md` | Session phases (research → feedback) |
| `AGENT_FEEDBACK.md` | End-of-session notes |
| `CODING_CONVENTIONS.md` | Agent coding index (points at product docs) |
| `BACKLOG.md` | **Harness** backlog only (not product features) |
| `traces/` | Task worksheets (optional) |
| `artifacts/` | INFRA_RUNBOOK + ephemeral CROSS_REVIEW (not long-term git history) |

**Not in this repo:** separate Python `core/` LLM runtime / `contracts/` skill executor (removed). The harness is **skills + scripts + pipeline FSM**.

## What is *not* product roadmap

- Pipeline FSM, pr_validator scores, skill authoring  
- ORCH / night_shift / worksheets  
- Vault logging policy for *agents* (`AGENTS.md` at repo root is session policy, not a user feature)

Product priorities: **`BACKEND_ROADMAP.md`** (product only) + **`docs/PRODUCT.md`**.

## Entry for agents

1. Product question → `docs/PRODUCT.md`, `migration/`  
2. How to ship a change → this README + `AGENT_WORKFLOW.md` + skill  
3. File boundaries → root `GEMINI.md` (routing; still labels product vs agent paths)  
4. Vault after product work → root `AGENTS.md`  

## Product boundary one-liner

> **Watchlist** = software users trade with. **`.agents`** = how AI operators develop that software.
