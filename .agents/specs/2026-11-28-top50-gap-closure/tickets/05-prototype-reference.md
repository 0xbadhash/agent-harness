# 05 — Prototype reference rule

**What to build:** a required reference declaration when a prototype is named, an import check, and the rule in the execute and plan docs.

**Kind:** feature
**Prefactor:** none
**Touches:** scripts/check_prototype_fidelity.py, templates/PR_DRAFT.md, skills/spec/references/spec-template.md, skills/execute_dev/SKILL.md, skills/spec/references/plan-template.md
**Blocked by:** None — can start immediately
**Status:** done

- [x] A named prototype without `**Prototype use:** reference` fails.
- [x] Source that imports `prototypes` fails.
- [x] The execute and plan docs state that prototype code is reimplemented.
