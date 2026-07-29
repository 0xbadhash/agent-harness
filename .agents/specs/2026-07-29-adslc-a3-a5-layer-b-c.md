# ADSLC next wave — A3–A5, Layer B (B1/B2 P0), Layer C

- **Product:** agent-harness
- **Created:** 2026-07-29
- **Status:** ready-for-agent
- **Priority:** P0 (B1/B2, A3–A5) · P1 (rest of B) · P2 (C3–C5 stretch)
- **Roadmap:** CHANGELOG.md → Open work
- **Plan:** `.agents/specs/2026-07-29-adslc-a3-a5-layer-b-c-plan.md`
- **Tickets:** `.agents/specs/2026-07-29-adslc-a3-a5-layer-b-c/tickets/`
- **Tracker:** local
- **Constitution:** AGENTS.md + policy defaults  
- **Depends on:** v1.4.5 hard gates pack (shipped)

## Problem Statement

Hard gates (v1.4.5) force evidence at score time, but operators still lack:

1. **Daytime CI** that runs the same hard readiness before night (A3)  
2. **Clean install** that removes deleted skills and stamps harness version (A4)  
3. **Structured task identity** on the pipeline (A5)  
4. **Spec-driven entry** and **AC↔test traceability** (B1/B2 — priority)  
5. Context, threat, release evidence (B3–B5)  
6. A **learning flywheel** for the agent OS itself (Layer C)

Without these, value plateaus: ships are gated but intent, continuity, portfolio learning, and install drift remain soft.

## Solution

Implement the remaining ADSLC program as **portable harness skills/scripts/docs**, in priority order, without adding new pipeline phases (five phases stay). Extra value is carried by **artifacts + score hooks + install/CI**, not a thicker FSM.

### Priority order for `/execute_dev` slices

| Order | ID | Priority | Outcome |
|-------|-----|----------|---------|
| 1 | **B1** | P0 | Spec gate (or waiver) before code `execute_dev` |
| 2 | **B2** | P0 | AC → tests → smoke table required in PR_DRAFT for code ships |
| 3 | **A3** | P0 | Daytime readiness wired for CI + documented operator cron |
| 4 | **A4** | P0 | Install `--delete-stale-skills` + `HARNESS_VERSION` stamp |
| 5 | **A5** | P0 | `pipeline.json` structured `task` / `spec_id` / `card_id` / `waiver` |
| 6 | **B3** | P1 | Context pack at ship start |
| 7 | **B4** | P1 | Threat-model mini-section when runtime/public surface |
| 8 | **B5** | P1 | Release evidence pack in RELEASE_RUNBOOK |
| 9 | **C1** | P1 | `/retrospect` skill after ship/night |
| 10 | **C2** | P1 | Skill/FSM self-tests in harness test suite (+ CI doc) |
| 11 | **C4** | P1 | Suggest `/qa_campaign` only when large-diff |
| 12 | **C3** | P2 | Night-shift failure taxonomy rollup script/report |
| 13 | **C5** | P2 | Lightweight agent skill-conformance eval (optional / spike) |

## User Stories

1. As an operator, I want PR CI to run daytime readiness, so night_shift is not the first signal.  
2. As an operator, I want reinstall to drop removed skills and record harness version.  
3. As an agent, I want `pipeline.json` to carry `spec_id` (or waiver), so hard gates and execute_dev share identity.  
4. As an operator, I want code work blocked without a linked spec (or explicit waiver).  
5. As a reviewer, I want AC IDs mapped to tests/smoke in PR_DRAFT before approve.  
6. As a multi-product owner, I want retrospect + taxonomy so harness improvements are data-driven.  
7. As an operator, I want qa_campaign suggested only for large ships, so small docs ships stay quiet.

## Implementation Decisions (what / why)

- **No new FSM phases** — keep `init|ready_for_review|approved|blocked|shipped`.  
- **B1:** enforce in `execute_dev` skill + optional `scripts/spec_gate.py` callable from bootstrap/CI; waivers mirror hard_gates vocabulary.  
- **B2:** extend `hard_gates.py` / PR_DRAFT checks for `## Traceability` or `AC-` table (code ships only).  
- **A3:** add `.github/workflows/daytime-gates.yml` (or `docs/` + example workflow) calling `daytime_readiness_subset.py`; document systemd/cron one-liner.  
- **A4:** `install_into_product.sh --delete-stale-skills` uses rsync `--delete` **only** under portable skill names from `ship_skills.txt` + harness skills dir listing (never wipe product-only skills). Write `.agents/HARNESS_VERSION`.  
- **A5:** extend `pipeline_state.set_phase` / get schema with optional keys; document; hard_gates may read `spec_id` from pipeline if PR_DRAFT missing.  
- **C4:** `next_skill` after sync_docs: large baseline → `/qa_campaign`, else `(done)` unless `--force-qa`.  
- Layer C skills stay **off-phase** (like night_shift / qa_campaign).

## Testing Decisions

- Unit tests per new script (spec_gate, install delete dry-run, pipeline schema, next_skill large→qa).  
- Extend `test_hard_gates` for B2 traceability.  
- Install bootstrap test: after install of fixture, deleted harness skill not present when --delete-stale-skills.  
- Self-tests (C2): phase illegal transition, next_skill after sync_docs, hard_gates CLI.  
- Smoke: harness product_smoke still green.

## Acceptance Criteria

### P0 (must ship in first execute slice set)

- [ ] **B1:** Documented + enforced: code `execute_dev` requires `**Spec:**` path that exists **or** `**Spec waiver:**` (hotfix|chore|docs-only|prose-only); helper script exits 0/1; skill text + optional pre-check  
- [ ] **B2:** Code ships require PR_DRAFT section **Traceability** (or equivalent) mapping each AC id/line to test and/or smoke; hard_gates fails without it (prose-only exempt)  
- [ ] **A3:** Example CI workflow + docs for `daytime_readiness_subset.py`; operator cron snippet in night-shift.md  
- [ ] **A4:** `install_into_product.sh --delete-stale-skills` removes only portable skills no longer in harness SoT; writes `HARNESS_VERSION` from harness `VERSION`; product-only skills preserved  
- [ ] **A5:** `pipeline.json` may store `spec_id`, `card_id`, `waiver` via `pipeline_state`; `get` round-trips them; docs updated  

### P1

- [ ] **B3:** `scripts/context_pack.py` or skill step writes `.agents/artifacts/CONTEXT_PACK.md` (constitution summary, open risks, last decisions placeholders)  
- [ ] **B4:** PR_DRAFT or hard_gates optional section **Threat notes** when runtime surface (assets + abuse cases bullets; fail if empty when runtime)  
- [ ] **B5:** `release_mgmt` skill + RELEASE_RUNBOOK template include smoke evidence table + optional coverage/SBOM links  
- [ ] **C1:** skill `retrospect` — inputs night/ship reports → `.agents/artifacts/RETRO.md` + optional vault note; no phase change  
- [ ] **C2:** harness tests for illegal phase, next_skill routes, hard_gates fail cases; documented in CI  
- [ ] **C4:** large-diff only `NEXT_SKILL=/qa_campaign` after sync_docs; small → `(done)`  

### P2

- [ ] **C3:** script rollup of NIGHT_SHIFT_REPORT fails → taxonomy markdown under artifacts or vault `harness-night-shift/`  
- [ ] **C5:** spike doc + minimal eval checklist (or skip with rationale if too heavy)  

### Cross-cutting

- [ ] CHANGELOG + ship-flow + skills-catalog + llm-bootstrap updated  
- [ ] Unit/integration tests green; product reinstall documented  
- [ ] No secrets; hard gates of this ship satisfied for code slices  

## Out of Scope

- New pipeline phases  
- Merging qa_campaign into night_shift  
- Full SBOM platform / commercial scanners as hard deps  
- Auto-merge of PRs from retrospect  
- Changing product domain code outside harness portability surface  
- Mandating 200-bug qa_campaign every cycle  

## Clarifications

### 2026-07-29 (from conversation — recommended defaults applied)

- Q: Implement full A3–A5 + Layer B + Layer C in one mega-PR?  
  - A: **No** — multi-ticket vertical slices; **B1/B2 first**, then A3–A5, then B3–B5, then C.  
- Q: New phases for spec?  
  - A: **No** — gate inside execute_dev + hard_gates / scripts.  
- Q: Spec waiver vocabulary?  
  - A: Align with hard gates: `hotfix|chore|docs-only|prose-only`.  
- Q: Install delete wipe product skills?  
  - A: **Never** — only portable skills that exist in harness SoT listing / ship_skills + known portable set.  
- Q: CI provider?  
  - A: GitHub Actions **example** workflow in-repo; products copy or reference.  
- Q: Threat / context fail closed?  
  - A: B3 soft generate; B4 hard when runtime (like behavior); B5 template hard at release skill text + soft score unless evidence empty.  
- Q: C5 full eval platform?  
  - A: P2 spike only; do not block P0/P1.  

## Further Notes

- Builds on hard gates pack; do not regress `hard_gates=25` semantics.  
- `daytime_readiness_subset.py` already exists (A3 is wire-up + docs + example workflow).  
- Product kanban card linkage (A5 `card_id`) is optional field; second-brain may populate later.  
- Risk: B1 too strict for drive-by chores → waiver path must be one line in PR_DRAFT / pipeline.  

## Handoff

```text
✅ SPEC READY
   spec:  .agents/specs/2026-07-29-adslc-a3-a5-layer-b-c.md
   plan:  .agents/specs/2026-07-29-adslc-a3-a5-layer-b-c-plan.md
   tickets: .agents/specs/2026-07-29-adslc-a3-a5-layer-b-c/tickets/
   next:  /execute_dev  (start ticket 01 — B1+B2)
   then:  remaining tickets → /code_review → … → /pr_review → /release_mgmt → /sync_docs
```
