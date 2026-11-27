# Plan — categorical lint bans

**Spec:** `.agents/specs/2026-11-27-categorical-lint-bans.md`

## Approach

Turn on the rule families in `ruff.toml`, let the existing ratchet freeze the
legacy counts, and make compliance use the ratchet instead of raw ruff. Separately,
ban blanket type suppressions and remove the ones mypy does not need, fixing the
few real errors with annotations and `cast`.

## Architecture

- `ruff.toml` owns rule selection and the mccabe threshold.
- `config/lint_ratchet_baseline.json` is the per-rule floor.
- `scripts/check_lint_ratchet.py` stays the pass/fail lint gate;
  `compliance_engine.py` calls it when present.
- `scripts/check_type_ignores.py` owns the suppression rule; `hard_gates` and
  `validate.py` call it.
- Mypy stays the type gate; no suppression is needed because
  `ignore_missing_imports = True` covers the sibling imports.

## Implementation sequence

1. Update `ruff.toml`, strip unneeded suppressions, and fix the eight mypy errors.
2. Add the suppression checker, its tests, and the gate wiring; record the ratchet
   floor.
3. Update compliance to use the ratchet and run the full verification set.

## Risks and rollback

- Risk: a product has no ratchet baseline. Mitigation: empty floor means only new
  findings fail; raw ruff remains the fallback when the script is absent.
- Risk: stripping a suppression hides a real type error. Mitigation: `mypy scripts
  tests` is clean and the full suite is green.
- Risk: compliance disagrees with CI. Mitigation: both call the same ratchet.
