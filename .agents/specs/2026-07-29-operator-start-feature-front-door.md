# Operator front door — start every feature with `/spec`

- **Product:** agent-harness
- **Created:** 2026-07-29
- **Status:** ready-for-agent
- **Priority:** P1
- **Roadmap:** CHANGELOG.md → Open work
- **Plan:** `.agents/specs/2026-07-29-operator-start-feature-front-door-plan.md`
- **Tickets:** `.agents/specs/2026-07-29-operator-start-feature-front-door/tickets/`
- **Tracker:** local
- **Constitution:** AGENTS.md + policy defaults  
- **Depends on:** v1.4.5 hard gates, v1.4.6 ADSLC (B1 spec_gate already exists)

## Problem Statement

Operators who just finished the hard-gates / ADSLC work still ask: **“When I start a new feature, what do I write?”**  

The answer lives in chat, not in a single first-class doc + scaffold:

- README/llm-bootstrap mention `/spec` but don’t spell the **minimum PR_DRAFT evidence** operators must fill  
- No one-command **scaffold** for “new feature” that creates Spec stub + PR_DRAFT with Spec / Traceability / Threat / Red-proof  
- Easy to jump to `/execute_dev` and hit `spec_gate` / hard_gates failures late  

## Solution

Make the **front door** obvious and mechanical:

1. **`docs/start-a-feature.md`** — canonical “write this” guide (normal / hotfix / docs-only)  
2. Link it from **README**, **llm-bootstrap**, **AGENTS template** as step 0  
3. **`scripts/start_feature.py`** — scaffolds:
   - optional `.agents/specs/<date>-<slug>.md` stub (from template)  
   - `PR_DRAFT.md` sections pre-filled with `**Spec:**` path or waiver  
   - prints next commands (`/spec` refine or `/execute_dev`)  
4. Install copies the doc into `.agents/docs/start-a-feature.md`  

Operators experience: one doc + one script → hard gates don’t surprise them mid-ship.

## User Stories

1. As an operator, I want a single doc that says “type `/spec …` for features,” so I don’t re-ask the agent.  
2. As an operator, I want a scaffold that creates Spec + PR_DRAFT with hard-gate placeholders, so score doesn’t fail on missing sections.  
3. As an agent, I want AGENTS.md / llm-bootstrap to point at that doc as the default front door.  
4. As an operator on a hotfix, I want the scaffold to support **Spec waiver: hotfix** without inventing a fake spec.

## Implementation Decisions

- **What/why only** in this ship: docs + thin CLI scaffold; no new FSM phase.  
- Reuse `templates/` for spec stub; extend PR_DRAFT template (already has Traceability/Threat).  
- `start_feature.py` is pure filesystem; no network.  
- Does not replace `/spec` skill — scaffolds **stub**, operator still runs `/spec` for full interview/clarify when needed, or edits stub then `/execute_dev`.  
- ADSLC mega-program already shipped (v1.4.6) — **out of scope** to re-implement here.

## Testing Decisions

- Unit test: `start_feature.py` creates files under temp root with `--slug` / `--waiver`.  
- Assert generated PR_DRAFT contains Spec or Spec waiver and `## Traceability`.  
- Manual: `python3 scripts/start_feature.py --help`; dry-run mode if easy.

## Acceptance Criteria

- [ ] `docs/start-a-feature.md` exists and covers: feature → `/spec`; hotfix → waiver; evidence table for hard gates; next slash commands  
- [ ] README + llm-bootstrap + `templates/AGENTS.harness.md` link to start-a-feature (or `.agents/docs/…` after install)  
- [ ] `scripts/start_feature.py` creates/updates PR_DRAFT with Spec path or waiver + Traceability stub  
- [ ] Optional `--write-spec-stub` writes `.agents/specs/<date>-<slug>.md` from template skeleton  
- [ ] `install_into_product.sh` copies `start-a-feature.md` into product `.agents/docs/`  
- [ ] Tests for start_feature green; harness smoke still green  
- [ ] No new pipeline phases; no secrets  

## Out of Scope

- Replacing `/spec` interview skill  
- Auto-running full FSM from start_feature  
- Product domain features (catalyxt news, etc.)  
- Re-opening finished ADSLC tickets (already v1.4.6)  

## Clarifications

### 2026-07-29 (from conversation)

- Q: What product?  
  - A: **agent-harness** (portable operator experience).  
- Q: Feature vs workflow meta?  
  - A: **Operator front door** for “start with `/spec`” after hard gates (chat synthesis).  
- Q: Force full `/spec` interview every time?  
  - A: **No** — scaffold + doc; full `/spec` when acceptance unclear.  
- Q: Hotfix path?  
  - A: **Yes** — `--waiver hotfix|chore|docs-only|prose-only`.  
- Q: Tickets?  
  - A: **Yes** — small vertical slices (doc vs script vs install).  

## Further Notes

- Complements `spec_gate.py` / hard_gates: this is **ergonomics**, those are **enforcement**.  
- Risk: operators treat stub as done without checkable AC — doc must say “refine acceptance before execute_dev.”  

## Handoff

```text
next:  /execute_dev  (ticket 01 docs first, or 02 script)
then:  /code_review → /pr_review --validate → /release_mgmt → /sync_docs
```
