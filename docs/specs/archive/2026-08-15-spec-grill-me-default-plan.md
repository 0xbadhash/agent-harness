# Plan: Grill-me default in `/spec`

- **Spec:** `docs/specs/2026-08-15-spec-grill-me-default.md`
- **Product:** agent-harness
- **Created:** 2026-08-15
- **Status:** ready-for-agent

## Stack & constraints

- Markdown skills + Python gates only
- No new product runtime; portable install copies `.agents/skills/spec/`

## Approach

1. Add grill-me checklist reference and rewrite `/spec` SKILL flow so interview+grill is default and non-skippable except `--spike`.
2. Template + docs so every new spec carries `## Grill-me`.
3. Deterministic `check_spec_grill.py` wired into `spec_gate` for feature Spec paths (not Spec waiver).
4. Unit tests for evidence rules.

## Architecture decisions

- Grill evidence lives **in the Spec file** (not a separate artifact) so AC map / hash stay simple.
- `spec_gate` calls grill check when Spec path resolves and no waiver.
- Spike: `## Grill-me` with `**Status:** spike-skipped` + reason ≥ 20 chars.

## File / surface map

| Area | Change |
|------|--------|
| `.agents/skills/spec/SKILL.md` | Mandatory grill-me flow; flags |
| `references/grill-me-checklist.md` | New |
| `references/spec-template.md` | Grill-me section |
| `references/clarify-checklist.md` | Cross-link grill |
| `scripts/check_spec_grill.py` | New gate |
| `scripts/spec_gate.py` | Invoke grill check |
| `docs/start-a-feature.md` | Operator front door |
| `docs/skills-catalog.md` | Catalog line |
| `tests/test_check_spec_grill.py` | Units |

## Implementation sequence

1. Checklist + template + SKILL.md  
2. check_spec_grill + spec_gate hook + tests  
3. Docs  

## Testing plan

- `python3 -m unittest tests.test_check_spec_grill`
- Manual: skill text grep for GRILL MISSING / --spike

## Risks & mitigations

| Risk | Mitigation |
|------|------------|
| Agents ignore skill | fail-closed grill check on ship |
| Question fatigue | theme N/A + recommended defaults |
