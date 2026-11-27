# 15 — Parallel ticket runner with one session per ticket

**What to build:** Run the unblocked ticket frontier in parallel, each in a fresh
worktree and session, and record the session ids.

**Kind:** feature
**Prefactor:** none
**Blocked by:** 03, 16
**Estimate:** 200
**Status:** ready-for-agent

- [ ] `scripts/run_tickets.py` reuses the DAG frontier and the stack layers
- [ ] `--workers N` runs at most N tickets, each in its own worktree
- [ ] Each run writes a session id and a status line; a failed ticket stops its
      dependents
- [ ] `pytest tests/test_stack_runners.py -q` covers frontier, worker limit, and
      dependent blocking
