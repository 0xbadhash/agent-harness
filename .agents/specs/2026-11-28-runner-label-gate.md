# Runner-label gate and post-release follow-ups

- **Product:** agent-harness
- **Created:** 2026-11-28
- **Status:** ready-for-agent
- **Priority:** P1
- **Roadmap:** CHANGELOG.md → Open work
- **Plan:** `.agents/specs/2026-11-28-runner-label-gate-plan.md`
- **Tickets:** `.agents/specs/2026-11-28-runner-label-gate/tickets`
- **Tracker:** local
- **Constitution:** AGENTS.md
- **Grill-me:** complete
- **Door:** two-way
- **Surface:** internal
- **Feature flag:** not-applicable (internal gate; no user-visible surface)
- **Prototype:** none
- **Prototype verdict:** not-applicable (no shape question; behavior is a lint exit code)

## Problem Statement

The workflow-harness PR gate defined both of its jobs with `runs-on: self-hosted`.
No self-hosted runner is attached to that repository, so the auto-merge job sat
`queued` on the two most recent PRs. Both merges succeeded because the check is
not required, which is the unsafe part: an operator sees an amber check, learns
to ignore it, and a gate that was meant to classify changes never runs.

The harness has no way to catch this class of mistake. A product can declare a
runner label that no machine has, and nothing fails until a job hangs. This
happened in one of the two repositories this harness ships to, so it will happen
again in another.

## Solution

The harness gets a portable check that compares the runner labels named in
`.github/workflows/*.yml` with a declared allowlist in
`.github/allowed-runners.txt`. A label that is used but not declared fails the
gate with the file, job, and label named. The check runs as a hard gate when a
repo has workflows and an allowlist, and skips with a stated reason otherwise.

workflow-harness fixes the immediate cause: both `review-tiers` jobs move to
`ubuntu-latest` (the workflow uses only `secrets.GITHUB_TOKEN` and the default
permissions block), it gains an allowlist naming `ubuntu-latest`, and its own
test enforces the same contract.

## User Stories

1. As an operator, I want a PR to fail when a workflow names a runner label the
   repository has not declared, so a dead job cannot merge silently.
2. As a maintainer, I want the failure to name the workflow file, the job, and
   the label, so the fix is a one-line edit rather than an investigation.
3. As a workflow maintainer, I want the review-tier jobs to run on a hosted
   runner, so the check completes instead of queueing forever.
4. As a release operator, I want the top-50 completion claim checked against the
   shipped commits, so the scorecard is evidence rather than assertion.

## Implementation Decisions

- **Reserved decisions:** release version numbers, closing the stale PRs,
  opening live GitHub issues, and running product installs.
- **Delegated decisions:** script name, allowlist path and format, gate id,
  message wording, and test seams.
- The harness ships `scripts/check_workflow_runners.py` and registers it in
  `hard_gates.py` as `workflow_runners`.
- The allowlist is plain text, one label per line, `#` comments allowed. An
  absent allowlist skips the gate; an empty one fails a repo that uses labels.
- workflow-harness carries its own small test because it does not vendor harness
  scripts; both implementations assert the same contract.
- The re-score and PR triage are read-only reports under `/srv/boxdrop/out/`.
  They change no repository and close nothing.

## Testing Decisions

- External behavior only: process exit code and the message naming the offending
  workflow, job, and label.
- Seams: `check_workflow_runners.check(root)` returns a list of findings;
  `main(["--root", ...])` returns 0 or 1.
- Fixtures build temporary repos with `.github/workflows/` and
  `.github/allowed-runners.txt` so no test depends on this repo's own workflows.
- Commands: `pytest tests/test_workflow_runners.py -q`,
  `pytest tests -q`, `scripts/validate.py full`, `scripts/product_smoke.py`.
- workflow-harness: `pytest tests/test_workflow_runners.py -q` and the full
  suite in that repo.

## Acceptance Criteria

- [ ] AC-1: `scripts/check_workflow_runners.py --root .` exits 0 when every
      `runs-on` label is declared, 1 otherwise, and names file, job, and label.
- [ ] AC-2: a repo with no `.github/workflows/` or no allowlist exits 0 with a
      stated skip reason; an empty allowlist fails a repo that uses a label.
- [ ] AC-3: `hard_gates.py` runs `workflow_runners` when the repo has both
      `.github/workflows/` and `.github/allowed-runners.txt`, and skips it
      with a stated reason otherwise.
- [ ] AC-4: workflow-harness `review-tiers.yml` jobs use `ubuntu-latest`, and its
      test rejects `self-hosted` unless it is declared in the allowlist.
- [ ] AC-5: `/srv/boxdrop/out/SCORECARD-GROKBUILD-HARNESS-TOP50-RESCORE-2026-11-28.md`
      pins both commits, gives a per-item verdict with evidence, and records a
      delta against the 2026-11-21 scorecard.
- [ ] AC-6: `/srv/boxdrop/out/TRIAGE-PRS-2026-11-28.md` records each open PR's
      supersession evidence and a close/revive recommendation.
- [ ] Product smoke commands succeed and no secrets are committed.

## Out of Scope

- Deleting the review-tier workflow or changing the auto-merge policy.
- Running `portfolio_install_report.py --install`; it needs per-product approval.
- Closing the stale PRs automatically; the operator approves the list.
- Opening live GitHub issues from the re-score gaps; drafts only.

## Grill-me

**Status:** complete
**Date:** 2026-11-28

### G1 Outcome
- Q: What outcome does the operator get?
  - A: A PR that names a runner no machine provides fails at PR time with the
    exact file, job, and label. The workflow-harness gate stops queueing.

### G2 Non-goal / kill
- Q: What is explicitly out?
  - A: Auto-merge policy, product installs, automated PR closure, and live issue
    creation. The challenge decision keeps these behind operator approval.

### G3 Wrong product
- Q: Could this be solved outside the harness?
  - A: workflow-harness needs its own fix regardless. The harness check exists so
    the next product does not repeat it.

### G4 Cheapest alternative
- Q: Why not just change the YAML?
  - A: The YAML change fixes one repo. The check is the part that prevents
    recurrence, and it is a small script plus one gate registration.

### G5 Abuse / failure
- Q: How could this fail?
  - A: A repo declares a label it does not have. The gate cannot know runner
    registration without an admin token, so the allowlist is a declaration of
    intent, and the skip reason states that limit.

### G6 Verify
- Q: How is it verified?
  - A: Unit tests with temporary repos, the harness's own gate run, the
    workflow-harness test, and the full suites. No runtime surface.

### G7 Priority
- Q: Why now?
  - A: The defect queued on the two PRs of the last ship. It is a one-line fix
    and a small gate, and it blocks trust in the PR check list.

### Pain ranking

1. A dead check that shows amber and is ignored.
2. A second product repeating the same declaration.
3. The re-score claim staying unverified.

## Clarifications

### 2026-11-28
- Q: Should the harness check query runner registration?
  - A: No. That needs an admin token and makes the check network-dependent. A
    declared allowlist is deterministic; the gate message states the limit.
- Q: Should the re-score skip items it cannot run?
  - A: No. It runs the named check where one exists and records the exit code;
    file inspection is allowed only where no check exists, and says so.
- Q: Do the stale PRs get closed in this ship?
  - A: The report recommends closure and gives evidence. Closing happens only
    after the operator approves the list.

## Further Notes

- Challenge record: `.agents/artifacts/CHALLENGE.md`; vault note at
  `01-Projects/agent-harness/challenges/2026-11-28-challenge-proposal-t2088u-followups.md`.
- The re-score is a read-only audit. Its only writes are the scorecard and the
  triage report under `/srv/boxdrop/out/`.
- Risk: `hard_gates.py` gains one gate. It is skipped unless the repo has
  workflows and an allowlist, so existing products see no change.

## Handoff

- Next: `/execute_dev` (three tickets; TDD for the gate)
- Then: `/code_review` → `/cross_review` → `/pr_review --validate` →
  `/release_mgmt` (agent-harness v1.5.2, workflow-harness v0.3.3) → `/sync_docs`
