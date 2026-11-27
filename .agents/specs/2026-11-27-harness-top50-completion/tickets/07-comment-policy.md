# 07 — Phased comment policy and comment-audit skill

**What to build:** A comment policy that starts with one directory, an audit
skill that wraps the checker, and a comment ratio in code review.

**Kind:** feature
**Prefactor:** none
**Blocked by:** None
**Estimate:** 170
**Status:** ready-for-agent

- [ ] `.agents/policy/comment-policy.md` defines why-only comments, the phased
      directory allowlist, and the ratchet
- [ ] `skills/comment_audit/SKILL.md` runs `check_comment_audit.py` with
      `--path`, `--diff`, `--baseline`, and `--ratio`
- [ ] `check_comment_audit.py --ratio` prints comment lines / code lines and
      `code_review` records the number
- [ ] `pytest tests/test_comment_and_docs.py -q` covers ratio and policy presence
