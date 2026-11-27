# CROSS-REVIEW — automation readiness gate

**Marker:** CROSS-REVIEW

- Base: `origin/main` · Head: `HEAD`
- Scope: `scripts/check_automation_ready.py`, `scripts/night_shift_autofix.py`,
  `scripts/night_shift_readiness.py`, `.agents/product_plugin.yaml`,
  `docs/night-shift.md`, `tests/test_automation_ready.py`, ship artifacts.
- Blocker count: **0**

## Security Guru

- No auth, network, or secret handling is added. The gate reads repository text
  and calls local checkers; `check_lint_ratchet` runs `ruff` with fixed arguments.
- Owner resolution reads `AUTOMATION_OWNER`; an operator could set a misleading
  name, but the value is recorded verbatim in the artifact and the PR draft, so
  the claim stays reviewable.
- Finding: none (blocker/major). Nit: `--require-artifact` trusts mtime; a
  restored artifact could pass freshness. Accepted because the artifact is
  regenerated from the same checkers and a future slice can hash the base commit.

## Maintainability Expert

- `check_automation_ready.py` follows the established `(ok, messages)` contract
  and keeps imports inside `check` so a product without a sibling script gets a
  named failure row.
- `_readiness_block` is one helper in the autofix module; the fixer set and the
  re-run path are unchanged.
- `night_shift_readiness.py` resolves the flag once and passes it through one
  call site.
- Finding: none (blocker). Nit: `_coverage_check` and `check_artifact` both
  compute artifact age; a shared `_age_hours` helper could remove the duplication
  once a third caller appears.

### Obsolete / cleanup (scoped)

Touched paths plus direct callers/callees only.

| Tier | Item | Confidence | Evidence |
|------|------|-----------|----------|
| A | none | — | `grep -rn "attempt_autofix\|check_automation_ready"` shows the readiness caller, the new tests, and the new CLI |
| B | none | — | no superseded readiness helper; `check_artifact` is the only reader of the marker |
| C | none | — | every branch (`blocked`, `ok`, missing checker) is reachable from tests |

## Domain Specialist

- Harness domain: a fail-closed gate must name the remedy and must default off
  for products. Both hold: every failure row states the command or file, and the
  plugin flag is opt-in with the harness as the reference proof.
- Finding: none (blocker). Note: the 24h cap assumes a daily cadence; a product on
  a slower schedule must set its own `--max-age-hours`.

## Follow-ups (not ship-blockers)

- Hash the base commit into the artifact so a restored file cannot pass freshness.
- Refresh the artifact from a green `validate.py full` to remove the manual step.

## Verdict

No blockers. Proceed to behavior validation and `/pr_review --validate`.
