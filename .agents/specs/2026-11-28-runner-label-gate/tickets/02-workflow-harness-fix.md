# 02 — workflow-harness runner fix

**What to build:** both `review-tiers.yml` jobs move to `ubuntu-latest`, the repo
declares `ubuntu-latest` in `.github/allowed-runners.txt`, and its tests enforce
that no workflow uses an undeclared label.

**Kind:** fix
**Prefactor:** none
**Blocked by:** 01
**Estimate:** 60
**Status:** ready-for-agent

- [ ] `docs-registry-auto-merge` and `send-money-human-review` use `ubuntu-latest`
- [ ] `.github/allowed-runners.txt` declares `ubuntu-latest` only
- [ ] `tests/test_workflow_runners.py` fails if a workflow names `self-hosted`
      or any other undeclared label
- [ ] `permissions: contents: write, pull-requests: write` and
      `secrets.GITHUB_TOKEN` are unchanged
- [ ] `pytest tests -q --ignore=tests/enhancement_specs` passes
- [ ] A PR run shows both review-tier jobs completing instead of queueing
