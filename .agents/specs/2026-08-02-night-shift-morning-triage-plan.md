# Plan — night-shift morning triage

## Surfaces

| File | Role |
|------|------|
| `scripts/night_shift_morning_triage.py` | CLI aggregate + optional recheck |
| `tests/test_night_shift_morning_triage.py` | fixtures |
| `deploy/morning-triage.service` + `.timer` | e.g. 00:30 UTC (08:30 HKT) after night 19:15 UTC |
| `scripts/install_morning_triage_timer.sh` | dry-run / --apply |
| `docs/night-shift.md` | operator section |
| `skills/night_shift/SKILL.md` | point to morning triage |

## Recheck

Call `daytime_readiness_subset.py --root <product>` for each FAIL product (bounded, no vault invent).

## Exit

`any_fail → 1` so systemd/cron can alert.
