# 10 — Process lens and reproduction command gate

**What to build:** A Process lens in cross review and a required `repro_cmd` for
defect fixes.

**Kind:** feature
**Prefactor:** none
**Blocked by:** None
**Estimate:** 140
**Status:** ready-for-agent

- [ ] `cross_review` adds a Process lens covering sessions, handoffs, retries,
      review cycles, and context loss
- [ ] `code_review` and `pr_review` require `repro_cmd` when the change fixes a
      defect, and `spec_gate` reports the missing field
- [ ] `pytest tests/test_comment_and_docs.py -q` covers the repro rule
