# Behavior contract — runner-label gate

**Marker:** BEHAVIOR-CONTRACT
**Surface:** `scripts/check_workflow_runners.py` CLI, the `hard_gates` diff run,
and workflow-harness CI. No web UI.
**Method:** each clause is judged by a command or a named test, not by reading
the implementation.

| # | Clause | Pass condition |
|---|--------|----------------|
| B1 | Declared labels pass | A repo whose jobs name only declared labels exits 0 and prints `ok: N workflow(s), M runner label(s) declared`. |
| B2 | Undeclared label fails | A job naming `self-hosted` against an allowlist of `ubuntu-latest` exits 1 and prints the workflow file, job, and label. |
| B3 | No workflows skips | A repo without `.github/workflows/` exits 0 with a skip reason naming the missing directory. |
| B4 | No allowlist skips | A repo with workflows but no `allowed-runners.txt` exits 0 with a skip reason naming the file; a used label is not failed. |
| B5 | Empty allowlist fails | A comment-only allowlist plus a used label exits 1 with one finding. |
| B6 | List `runs-on` checks every entry | `[ubuntu-latest, gpu-box]` fails on `gpu-box` only. |
| B7 | Expression is unresolved, not a failure | `${{ matrix.os }}` exits 0 and reports one unresolved expression. |
| B8 | Unparsable workflow fails with a reason | Invalid YAML exits 1 with reason `cannot parse workflow`. |
| B9 | Hard-gate integration | A non-prose diff on a repo with both inputs reports `skip workflow_runners (N workflow(s) declared)` and does not change the pass/fail of an otherwise clean diff. |
| B10 | workflow-harness uses hosted runners | Both `review-tiers.yml` jobs name `ubuntu-latest`; the repo's three tests pass. |

## Out of scope

- Resolving matrix expressions to concrete labels.
- Detecting whether a declared runner is actually attached.
- Any network or GitHub API call.
