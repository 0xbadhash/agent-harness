# 11 — Docs pattern sweep

**What to build:** Remove docs that teach rejected patterns and add a check that
keeps them out.

**Kind:** feature
**Prefactor:** none
**Blocked by:** 07, 08
**Estimate:** 120
**Status:** ready-for-agent

- [ ] Rejected patterns are named in one list with their replacement
- [ ] `scripts/check_docs_patterns.py` scans `docs/` and `skills/` against the
      list with an allowlist for historical notes
- [ ] `pytest tests/test_comment_and_docs.py -q` covers a hit and an allowlisted hit
