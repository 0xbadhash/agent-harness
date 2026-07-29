# Plan — ADSLC A3–A5 + Layer B + Layer C

**Spec:** `.agents/specs/2026-07-29-adslc-a3-a5-layer-b-c.md`

## Architecture principles

1. Five FSM phases unchanged.  
2. Prefer scripts + hard_gates extensions over new phases.  
3. Product-only skills never deleted by install.  
4. B1/B2 before cosmetics.

## Slice design

### Ticket 01 — B1 + B2 (P0)

| Piece | How |
|-------|-----|
| `scripts/spec_gate.py` | Check PR_DRAFT or env/pipeline for Spec path exists or waiver; exit 0/1 |
| `skills/execute_dev/SKILL.md` | Pre-condition: run spec_gate for non-docs; halt SPEC MISSING / WAIVER REQUIRED |
| `scripts/hard_gates.py` | Add traceability check: `## Traceability` table or lines matching `AC-\d+` / checklist mapped to test/smoke |
| PR_DRAFT template | Add Traceability section stub |
| Tests | test_spec_gate.py, extend test_hard_gates.py |

### Ticket 02 — A3–A5 (P0)

| Piece | How |
|-------|-----|
| A3 | `.github/workflows/daytime-gates.yml` (workflow_dispatch + pull_request optional); night-shift.md cron example |
| A4 | install: `--delete-stale-skills` builds allowlist = names under harness `skills/` + ship_skills; rsync delete only those dirs under product `.agents/skills/`; write `VERSION` → `.agents/HARNESS_VERSION` |
| A5 | `pipeline_state`: set/get extra keys `spec_id`, `card_id`, `waiver` without breaking old JSON; CLI flags |
| Tests | install bootstrap with delete; pipeline_state round-trip |

### Ticket 03 — B3–B5 (P1)

| Piece | How |
|-------|-----|
| B3 | `scripts/context_pack.py` → CONTEXT_PACK.md; execute_dev step optional |
| B4 | hard_gates: if runtime, require `## Threat notes` (≥2 bullets) in PR_DRAFT |
| B5 | release_mgmt skill + RELEASE_RUNBOOK template section Evidence pack |

### Ticket 04 — C1 C2 C4 (P1)

| Piece | How |
|-------|-----|
| C1 | `skills/retrospect/SKILL.md` + thin script optional |
| C2 | tests/test_fsm_conformance.py (phases, next_skill, hard_gates CLI) |
| C4 | next_skill after sync_docs: if large (review_scope) → qa_campaign else done; `--force-qa` |

### Ticket 05 — C3 C5 (P2)

| Piece | How |
|-------|-----|
| C3 | `scripts/night_shift_taxonomy.py` parse NIGHT_SHIFT_* reports |
| C5 | `docs/agent-eval-spike.md` + checklist only unless time allows one automated check |

## Risks

| Risk | Mitigation |
|------|------------|
| Install --delete removes product skill | Allowlist portable only; never delete unknown dirs |
| B1 blocks chores | Waiver one-liner |
| CI too slow | daytime subset product list filter `--only` |

## Verify

```bash
python3 -m pytest tests/ -q
python3 scripts/hard_gates.py --diff HEAD~1...HEAD
python3 scripts/daytime_readiness_subset.py --root .
bash install_into_product.sh /tmp/t --verify --delete-stale-skills
```
