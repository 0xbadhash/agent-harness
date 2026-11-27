# 04 — Make retro and QA produce issue bodies

**What to build:** Retro clusters become one Markdown issue body each plus an
umbrella issue. The default path stays offline; `gh` runs only with explicit
opt-in.

**Blocked by:** 01

**Status:** ready-for-agent

- [ ] `retro_job.py --file-issues` writes one body per cluster and one umbrella body.
- [ ] `retro_job.py` makes no subprocess call without `--gh`.
- [ ] `--gh` requires `--file-issues` and uses an argv list.
- [ ] `/qa_campaign` documents the same issue-body flow.
