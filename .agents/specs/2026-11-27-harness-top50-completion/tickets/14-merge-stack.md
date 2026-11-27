# 14 — Ordered stack merge runner

**What to build:** Merge an approved stack in dependency order in the background,
stopping on the first red check, with opt-in auto-merge.

**Kind:** feature
**Prefactor:** none
**Blocked by:** 16
**Estimate:** 180
**Status:** ready-for-agent

- [ ] `scripts/merge_stack.py` reads the stack plan layers and a PR-number map
- [ ] `--dry-run` prints the order; a red or unknown check stops the run
- [ ] `--auto-merge` calls `gh pr merge --auto --squash`; default stops for the
      operator after each merge
- [ ] `pytest tests/test_stack_runners.py -q` covers order, stop-on-red, and dry run
