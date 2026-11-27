# Comment policy

Comments explain **constraints a reader cannot see from the code**: a protocol
quirk, a rate limit, a safety rule, a workaround with an owner. They do not
narrate history, restate the next line, or excuse a skipped check.

## Allowed

- Why a non-obvious constant, ordering, or guard exists.
- A workaround that names the check or issue that bounds it
  (`scripts/…`, `tests/…`, `check:_`, `TODO(name)`).
- A pointer to an ADR or spec that explains a surprising choice.

## Forbidden

- History: "previously", "used to", "no longer", "removed".
- Commented-out code.
- Ownerless `TODO`.
- Escape hatches without a bound: "for now", "temporary", "safe to ignore".

## Phased rollout

Phase 1 (this ship) covers `scripts/` and `skills/`. Phase 2 extends to
`tests/` once the baseline is stable. Other directories are advisory until
their phase starts.

The allowlist for a phase lives here as a bullet list; `check_comment_audit.py
--diff` enforces the added lines in every covered path.

## Ratchet

Whole-tree runs compare against `config/comment_audit_baseline.json`; findings
may fall but never rise. Update the floor only with
`python3 scripts/check_comment_audit.py --root . --baseline
config/comment_audit_baseline.json --update-baseline`, and say why in the commit.

## Metric

`python3 scripts/check_comment_audit.py --ratio` prints comment lines / code
lines. The ratio is evidence, not a target: a rising ratio with no new
constraints is a smell, and so is a hard constraint with no comment at all.
