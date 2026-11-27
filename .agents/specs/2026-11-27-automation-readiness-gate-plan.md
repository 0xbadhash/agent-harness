# Plan — automation readiness gate

**Spec:** `.agents/specs/2026-11-27-automation-readiness-gate.md`

## Approach

Prove the inner loop as data: one script evaluates the five preconditions and
records a timestamped artifact. The outer loop reads only the artifact, so the
per-night decision is cheap and the evidence is inspectable.

## Architecture

- `scripts/check_automation_ready.py` owns `check`, `write_artifact`,
  `check_artifact`, and `resolve_owner`.
- `scripts/night_shift_autofix.py` gains `require_readiness`; `_readiness_block`
  turns a failed artifact into one `autofix_blocked` record.
- `scripts/night_shift_readiness.py` resolves the flag from
  `night_shift.require_automation_ready` or `AUTOFIX_REQUIRE_READY`.
- `.agents/product_plugin.yaml` opts the harness in.
- `.agents/docs/night-shift.md` documents refresh and validation commands.

## Implementation sequence

1. Add the gate script and unit tests for every precondition and the artifact.
2. Wire `require_readiness` through the autofix and readiness entry points.
3. Opt in via the plugin, document the commands, record the artifact, and run the
   full verification set.

## Risks and rollback

- Risk: a product has no coverage artifact. Mitigation: the flag is off by
  default; a product that opts in must produce coverage.
- Risk: the artifact goes stale between runs. Mitigation: the 24h cap matches the
  nightly cadence, and the refusal message names the refresh command.
- Risk: the gate becomes a second source of truth. Mitigation: it calls the same
  ratchet, suppression, and correction checkers as `hard_gates`.
