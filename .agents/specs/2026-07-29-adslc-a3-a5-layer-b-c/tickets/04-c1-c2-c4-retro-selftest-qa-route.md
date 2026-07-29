# Ticket 04 — C1 Retrospect + C2 FSM self-tests + C4 qa_campaign large-only (P1)

**Status:** open  
**Blocked by:** none  
**Spec:** `.agents/specs/2026-07-29-adslc-a3-a5-layer-b-c.md`

## Goal

Post-ship retrospect skill; automated FSM/skill conformance tests; suggest qa_campaign only on large post-sync_docs.

## Acceptance

- [ ] skills/retrospect/SKILL.md  
- [ ] tests/test_fsm_conformance.py (or equivalent)  
- [ ] next_skill sync_docs → qa only if large; --force-qa  
- [ ] catalog + ship-flow updated  
