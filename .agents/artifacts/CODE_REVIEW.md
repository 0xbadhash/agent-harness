# CODE-REVIEW — categorical lint bans

**Marker:** CODE-REVIEW

- Command: `python3 scripts/next_skill.py --after execute_dev --base origin/main --head HEAD`
- Base: `origin/main` · Head: `HEAD`
- Secrets scan: covered by `hard_gates` (`check_secrets_diff.py`)

## Standards

- `check_type_ignores.py` follows the `(ok, messages)` contract and uses the same
  skip-dir set as the other scanners.
- The suppressed files were edited mechanically; the eight fixes use `Any`,
  `Callable | None`, and `cast` rather than new suppressions.
- `compliance_engine.py` prefers the ratchet and keeps raw ruff as a product
  fallback, so a product without the script still gets a lint result.
- `ruff.toml` keeps `E501`/`E402` ignored for the documented CLI/test reasons.
- No P0 findings.

## Spec

- AC-1 is `tests/test_lint_config.py`.
- AC-2 is `tests/test_lint_ratchet.py` plus the `--update` run.
- AC-3 is `tests/test_type_ignores.py`.
- AC-4 is the live tree (zero suppressions) and `mypy scripts tests` success.
- AC-5 is `tests/test_hard_gates.py::test_type_ignores_blocks_code_ship`.
- AC-6 is `validate.py full` 9/9.
- AC-7 is the full suite, smoke, and the diff secrets scan.
- Scope matches the spec; no unrelated style churn.

## Correction checks

- A new blind except could pass → `config/lint_ratchet_baseline.json` + tests/test_lint_ratchet.py
- Complexity could creep → ruff C901 + ratchet
- A blanket suppression could return → tests/test_type_ignores.py
- An expired suppression could linger → tests/test_type_ignores.py::test_expired_fails
- Compliance could disagree with CI → the lint ratchet gate in scripts/compliance_engine.py
- Gate wiring could be silent → tests/test_hard_gates.py

## Findings

- P0: none.
- Follow-ups: the 44 `BLE001` and 14 `C901` findings are frozen; a later slice can
  burn them down and lower the baseline.

## Verdict

Approve. The targeted tests went red first (missing module and config), the full
suite is green, mypy is clean without suppressions, and validate is 9/9.
