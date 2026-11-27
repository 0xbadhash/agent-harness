# 01 — Wire the five orphaned helpers

**What to build:** Every existing helper (retro job, smart-zone guard, compact
safety, comment audit, ticket DAG) is invoked by the skill or CI job that owns
its stage.

**Blocked by:** None

**Status:** ready-for-agent

- [ ] `/execute_dev` runs `check_ticket_dag.py` on the task tickets and halts on a cycle.
- [ ] `/execute_dev` runs `smart_zone_guard.py` before a long handoff and `check_compact_safety.py` before compaction.
- [ ] `/code_review` runs `check_comment_audit.py` on the diff with `--strict`.
- [ ] `/retrospect` runs `retro_job.py`.
- [ ] CI runs the comment audit on the pull-request diff and the ticket DAG on every spec tickets directory.
