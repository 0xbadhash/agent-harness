# 08 — JS/TS lint ratchet and comment-to-test migration

**What to build:** A ratcheted ESLint template for product repos, and a rule that
moves constraints out of comments into test names.

**Kind:** feature
**Prefactor:** none
**Blocked by:** 07
**Estimate:** 150
**Status:** ready-for-agent

- [ ] `templates/eslint-ratchet/` carries a config, a violation baseline, and a
      README with the update command
- [ ] `docs/tdd.md` states the comment-to-test-name migration rule with an example
- [ ] `code_review` checks for untested constraints stated only in comments
- [ ] `pytest tests/test_comment_and_docs.py -q` asserts the template and docs
