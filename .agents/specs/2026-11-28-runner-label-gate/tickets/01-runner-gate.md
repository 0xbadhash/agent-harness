# 01 — Harness runner-label gate

**What to build:** `scripts/check_workflow_runners.py` compares the runner labels
named in `.github/workflows/*.yml` with `.github/allowed-runners.txt` and fails
on an undeclared label. `hard_gates.py` runs it as gate `workflow_runners`.

**Kind:** feature
**Prefactor:** none
**Blocked by:** None
**Estimate:** 140
**Status:** ready-for-agent

- [ ] A temporary repo whose workflow uses a declared label exits 0
- [ ] An undeclared label exits 1 and the message names workflow, job, and label
- [ ] No workflows, or no allowlist, exits 0 with a stated skip reason
- [ ] An empty allowlist fails a repo that uses a label
- [ ] A list-valued `runs-on` checks every entry; an expression is reported
      unresolved and does not fail
- [ ] `hard_gates.py` runs the gate when workflows and an allowlist exist and
      skips with a reason otherwise
- [ ] `pytest tests/test_workflow_runners.py -q` and `pytest tests -q` pass
