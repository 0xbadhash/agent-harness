# PR Draft — A3 daytime ops wire-up (ticket 01)

**Range:** 2572cea..HEAD  
**Spec:** `.agents/specs/2026-07-29-adslc-a3-b5-c5-harden.md`  
**Ticket:** `.agents/specs/2026-07-29-adslc-a3-b5-c5-harden/tickets/01-a3-daytime-ops.md`

## What Problem This Solves

Daytime readiness existed as GHA + cron docs only; operators lacked installable systemd units, a wiring check, and a product GHA template — so night_shift was still the first multi-product automated signal on many hosts.

## Why This Change Was Made

Mirror proven `night-shift-all` deploy pattern; keep enable opt-in (`--apply`); add deterministic `check_daytime_wiring.py`.

## User Impact

Operators can dry-run then enable daytime-gates.timer; products can copy `templates/daytime-gates.yml`.

## Evidence pack

| Item | Result |
|------|--------|
| hard_gates | run at pr_review |
| unittest | tests.test_daytime_wiring 4 OK |
| validate full | 5/5 |
| product_smoke | 2/2 |
| wiring check | ok=True |

## Evidence

```text
red_cmd: python3 -m unittest tests.test_daytime_wiring  # failed before implement (import/missing)
green_cmd: python3 -m unittest tests.test_daytime_wiring
```

## Red-proof

- red_cmd: `python3 -m unittest tests.test_daytime_wiring` (missing module / files before green)
- green_cmd: `python3 -m unittest tests.test_daytime_wiring`

## Traceability

| AC | Test / smoke |
|----|----------------|
| AC-1 deploy service+timer | files present; wiring check |
| AC-2 install dry-run/--apply | install_daytime_timer.sh dry-run exit 0 |
| AC-3 check_daytime_wiring | tests/test_daytime_wiring.py |
| AC-4 product template | templates/daytime-gates.yml |
| AC-5 docs | night-shift.md, ship-flow.md |

## Threat notes

- **Asset:** systemd timer running multi-product smoke as host user  
- **Abuse:** premature enable without review — mitigated by default dry-run + sudo  
- **Abuse:** malicious product path in night_shift_products.yaml — pre-existing; same as night-shift  

## Things that look bad but are actually fine

1. Host absolute paths in deploy units — same pattern as night-shift-all.service (documented host layout).
2. Timer not enabled on host in this release — install defaults to dry-run; operator must `--apply`.
3. start_feature F541 fix appears adjacent — required for validate full linter green on this repo.
