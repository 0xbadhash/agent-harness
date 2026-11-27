# 01 — ADR spine and reserved/delegated decisions

**What to build:** An ADR folder with an index and template that the grill reads
before asking, plus reserved/delegated decision fields in the spec and plan.

**Kind:** feature
**Prefactor:** none
**Blocked by:** None
**Estimate:** 180
**Status:** ready-for-agent

- [ ] `.agents/decisions/README.md` indexes every `NNN-*.md` ADR and its status
- [ ] `.agents/decisions/000-template.md` carries reversibility, surprise, tradeoff
- [ ] `scripts/check_adr.py` fails on a broken index, missing file, or an ADR
      that states none of the three parts; `--strict` also fails on empty index
- [ ] `/spec` §0 reads relevant ADRs and §3 only proposes an ADR when the three
      criteria hold and the operator agrees
- [ ] `spec-template.md` and `plan-template.md` carry `**Reserved decisions:**`
      and `**Delegated decisions:**`
- [ ] `pytest tests/test_decisions_and_review.py -q` covers pass and fail cases
