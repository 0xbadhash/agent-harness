# 06 — Grill modes and glossary-derived data model

**What to build:** A batch/serial grill switch recorded in the spec, and a plan
term-to-entity table derived from glossary terms with a deletion policy.

**Kind:** feature
**Prefactor:** none
**Blocked by:** 01
**Estimate:** 130
**Status:** ready-for-agent

- [ ] `/spec --mode batch|serial` records the mode and any mid-grill switch
- [ ] `plan-template.md` carries a `## Data model` table (term, entity, owner)
      and `**Deletion policy:**`
- [ ] `spec_gate.py` reports a plan whose data-model terms are absent from
      `GLOSSARY.md` when both exist
- [ ] `pytest tests/test_prototype_and_handoff.py -q` covers mode and data model
