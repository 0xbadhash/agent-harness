# 05 — Add a stack planner and review chunks

**What to build:** A deterministic planner turns ticket `Blocked by:` edges into
ordered implementation layers and review chunks, and the planning/review skills
use it.

**Blocked by:** 01

**Status:** ready-for-agent

- [ ] `scripts/stack_plan.py` emits topological layers for a ticket directory.
- [ ] The planner exits non-zero on a dependency cycle and reports the cycle.
- [ ] `--write` emits `.agents/artifacts/STACK_PLAN.md` and `.json`.
- [ ] `/execute_dev` plans layers for multi-ticket ships and `/code_review` reviews each layer as a chunk.
