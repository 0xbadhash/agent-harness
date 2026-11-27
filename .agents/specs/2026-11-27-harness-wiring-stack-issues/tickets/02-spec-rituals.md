# 02 — Tighten the spec ritual

**What to build:** The grill asks why before what, ranks pain, and accepts a
`STOP` token; the clarify pass proves candidate names against scenarios; the
spec gate fails on colliding glossary terms.

**Blocked by:** None

**Status:** ready-for-agent

- [ ] `grill-me-checklist.md` documents the operator `STOP` token, why-first order, and pain ranking.
- [ ] `clarify-checklist.md` documents a candidate-name scenario table.
- [ ] `skills/spec/SKILL.md` points to all four rituals.
- [ ] `spec_gate.py` returns a failure for normalized glossary collisions and passes for distinct terms.
