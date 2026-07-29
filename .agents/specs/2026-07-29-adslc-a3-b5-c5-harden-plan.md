# Plan — ADSLC A3 / B5 / C5 harden

- **Spec:** `.agents/specs/2026-07-29-adslc-a3-b5-c5-harden.md`
- **Stack:** Python 3 scripts, systemd units, GHA YAML, unittest/pytest
- **Order:** ticket 01 → 02 → 03 (each full ship)

## Ticket 01 — A3 daytime ops

| Surface | Change |
|---------|--------|
| `deploy/daytime-gates.service` | oneshot: `daytime_readiness_subset.py` multi-product |
| `deploy/daytime-gates.timer` | e.g. 18:00 UTC daily |
| `scripts/install_daytime_timer.sh` | copy units to `/etc/systemd/system`, daemon-reload, enable on `--apply` |
| `scripts/check_daytime_wiring.py` | exit 0/1 report |
| `templates/daytime-gates.yml` | product workflow template |
| docs | night-shift.md, ship-flow snippet |
| tests | `tests/test_daytime_wiring.py` |

## Ticket 02 — B5 evidence pack gate

| Surface | Change |
|---------|--------|
| `scripts/hard_gates.py` | `## Evidence pack` required for non-prose |
| `tests/test_hard_gates.py` | fail without / pass with |
| `skills/release_mgmt/SKILL.md` | keep + align wording |
| `templates/PR_DRAFT.md` | Evidence pack section shape |

## Ticket 03 — C5 eval runner

| Surface | Change |
|---------|--------|
| `scripts/agent_eval_checklist.py` | runnable checklist |
| `tests/test_agent_eval_checklist.py` | unit |
| `docs/agent-eval-spike.md` | runner usage |
| `.github/workflows/daytime-gates.yml` | optional step |

## Risks

- Deploy units with host paths may trip hardcode scanner — allowlist or match night-shift pattern.
- B5 too strict for chores — prose-only / waiver path already skips heavy code gates; Evidence pack only for non-prose.
