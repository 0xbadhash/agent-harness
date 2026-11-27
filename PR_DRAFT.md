# PR Draft: Markdown escape hatch — prose must name a check

**Range:** `origin/main..HEAD`

## What Problem This Solves

Agents wrote justifications into comments, skills, and `AGENTS.md` (“for now”,
“temporary”, “safe to ignore”). Those lines were not enforceable, `AGENTS.md` had
no hard line cap on this branch, and `## Do not` bullets named no check. The
comment audit also ran only in `hard_gates`, not `validate.py`.

## Why This Change Was Made

The gate pack should refuse prose that justifies skipping a check. The Markdown
audit names the offending line and the edited sections now cite the check that
enforces each prohibition.

## User Impact

- `/pr_review --validate` and `validate.py full` fail on a new escape-hatch
  comment or an unenforced `## Do not` bullet.
- `AGENTS.md` above 250 lines fails `check_stale_agent_config` and `validate.py`.
- The legacy comment set is frozen in `config/comment_audit_baseline.json`; new
  findings fail, declines are welcome.
- `[DEBUG-…]` tags in Python now fail repo hygiene, matching the existing skill
  promise.

## Evidence pack

| Gate | Command | Result |
|------|---------|--------|
| Red proof | `python3 -m pytest tests/test_markdown_audit.py tests/test_comment_audit.py -q` | `ModuleNotFoundError: check_markdown_audit`; `escape_hatch` assertion failed |
| Targeted tests | same command after implementation | 42 passed, 11 subtests |
| Full suite | `python3 -m pytest -q` | 497 passed, 2 skipped |
| Smoke | `python3 scripts/product_smoke.py --root .` | 2/2 steps passed |
| Validate | `python3 scripts/validate.py full` | 8/8 gates passed |
| Hard gates | `python3 scripts/pr_validator.py --diff origin/main...HEAD` | pr_validator score 100 |

**Spec:** `.agents/specs/2026-11-27-markdown-escape-hatch-audit.md`
**Plan:** `.agents/specs/2026-11-27-markdown-escape-hatch-audit-plan.md`

## Traceability

| AC | Test / smoke |
|----|----------------|
| AC-1 escape-hatch comments fail | `tests/test_comment_audit.py::TestJustificationAudit` |
| AC-2 baseline ratchet | `tests/test_comment_audit.py::test_baseline_ratchet` |
| AC-3 AGENTS.md cap | `tests/test_markdown_audit.py::TestAgentsBloat` |
| AC-4 `## Do not` enforcement | `tests/test_markdown_audit.py::TestDoNotEnforcement` |
| AC-5 bullets vs table rows | `tests/test_markdown_audit.py::TestEscapeHatches` |
| AC-6 validate wiring | `python3 scripts/validate.py full` → 8/8 |
| AC-7 DEBUG tags fail | `tests/test_repo_hygiene.py::test_debug_tag_fails` |
| AC-8 suite/smoke/validate + secrets | full pytest 497 passed; smoke 2/2; `check_secrets_diff.py` |

## Threat notes

Security tags: `secrets`, `supply-chain`, `injection`.

- Asset / trust boundary: the scanners read repository text only; they execute no
  network call and no shell from scanned content.
- Abuse case: prose that names a `scripts/…` file to bypass the `escape_hatch`
  class could cite a nonexistent check; `check_stale_agent_config` resolves
  `scripts/` references and fails on missing files (`supply-chain` integrity).
- Abuse case: an `AGENTS.md` cap could be gamed by moving prose into skills;
  skills carry the same justification rule and the `## Do not` requirement.
- Abuse case: baseline could hide new findings in a known file; the ratchet is
  per `path::kind`, so a new finding in a known file raises its key count.
- Abuse case: debug tags could leak payloads; the new `[DEBUG-` rule fails the
  diff before commit, alongside the `secrets` scan.

## Red-proof (process honesty)

Red was observed before implementation: the targeted run failed collection with
`ModuleNotFoundError: No module named 'check_markdown_audit'`, and the
`escape_hatch` assertion failed because the class did not exist. The retained
green command is executable:

```text
green_cmd: python3 -m pytest tests/test_markdown_audit.py tests/test_comment_audit.py tests/test_repo_hygiene.py tests/test_hard_gates.py -q
```

## Things that look bad but are actually fine

1. `config/comment_audit_baseline.json` lists seven legacy findings. It is a
   ratchet floor, not an allowlist for new prose.
2. `check_markdown_audit.py` prints `ok: no AGENTS.md` in this repo. The cap is
   exercised by tests and applies to products that carry the file.
3. The comment audit prints excess keys without line text; the follow-up is named
   in CODE_REVIEW.md and does not change the pass/fail result.
