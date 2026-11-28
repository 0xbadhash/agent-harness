# 02 — Comment audit routes and constraint rule

**What to build:** classification of each comment into delete, move-to-ADR, move-to-test-name, or rewrite; an opt-in constraint check; and a skill that applies the table with operator approval.

**Kind:** feature
**Prefactor:** none
**Touches:** scripts/check_comment_audit.py, skills/comment_audit/SKILL.md, docs/tdd.md
**Blocked by:** None — can start immediately
**Status:** done

- [x] `--classify` prints a route for every finding.
- [x] `--constraints` fails a constraint comment with no test name, check reference, or `waive:` reason.
- [x] The skill and `docs/tdd.md` state the migration rule and the approval step.
