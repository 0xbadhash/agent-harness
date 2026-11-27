# 19 — workflow-harness ordered stack with registry last

**What to build:** Require workflow changes to land as an ordered stack with the
registry change last.

**Kind:** feature
**Prefactor:** none
**Blocked by:** 17
**Estimate:** 90
**Status:** ready-for-agent

- [ ] The ticket DAG check enforces registry-last for workflow stacks
- [ ] `specs/` and the workflow docs describe the order
- [ ] The workflow-harness test suite covers a registry-early failure
