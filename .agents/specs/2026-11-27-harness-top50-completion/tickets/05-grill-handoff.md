# 05 — Compact grill handoff and research subagent

**What to build:** A compact handoff artifact written before AFK work, and a
read-only research subagent the spec skill launches while the operator answers.

**Kind:** feature
**Prefactor:** none
**Blocked by:** 01
**Estimate:** 170
**Status:** ready-for-agent

- [ ] `context_pack.py --compact` writes `GRILL_HANDOFF.md` with decisions,
      glossary changes, ADR links, prototype verdict, and open questions
- [ ] `/spec` §2 names a read-only research subagent and requires `## Research`
      plus `RESEARCH_NOTES.md`
- [ ] `pytest tests/test_prototype_and_handoff.py -q` asserts every handoff
      section and the research note path
