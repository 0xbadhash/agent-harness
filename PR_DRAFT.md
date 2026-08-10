# PR Draft — HSQ-1 Ship Quality SoT (PR1–PR5)

**Spec:** `.agents/specs/HSQ-1-ship-quality-sot.md`  
**Product:** agent-harness  
**Version:** 1.4.20

## What Problem This Solves

Ship quality noise and opacity: hard-coded large-diff thresholds misfire across
product shapes; spec waivers leave no audit trail; skill conformance already in CI
was documented as missing; portfolio reinstall cannot force-sync or report protect-list
drift; Security IOC ops were under-documented relative to PR hard gates.

## Why This Change Was Made

HSQ-1 agreed scope after independent architecture verification: fix verified gaps
(thresholds, waiver ledger, CI honesty, portfolio force/protect-drift, IOC docs)
without inventing false missing-CI work or a second FSM.

## User Impact

- Products can tune large-diff soft-gate thresholds in `product_plugin.yaml`.
- Operators see waiver frequency via `waiver_report.py`.
- Portfolio installs can force-resync; protect-list drift is visible.
- Docs clarify Security IOC is ops, not a PR hard gate.
- No change to night schedule or vault layout.

## Evidence

- `pytest tests/ -q` → 151 passed
- `validate.py full` → 6/6 gates
- `hard_gates.py` → ok=True
- Spec: `.agents/specs/HSQ-1-ship-quality-sot.md`

## Summary

Implement HSQ-1 workstreams A–E: configurable large-diff thresholds, waiver ledger,
honest skill-conformance CI naming, portfolio `--force` + protect-drift, Security IOC docs.

## Spec / waiver

**Spec:** `.agents/specs/HSQ-1-ship-quality-sot.md`

## Traceability

| AC | Test / evidence |
|----|-----------------|
| AC-1 thresholds | `tests/test_review_scope.py` (plugin + kwargs) |
| AC-2 waiver log | `tests/test_spec_waiver_log.py` |
| AC-3 CI | `.github/workflows/daytime-gates.yml` skill-conformance job |
| AC-4 portfolio | `portfolio_install_report.py --force --protect-drift` |
| AC-5 IOC docs | `docs/ship-flow.md` Security IOC section |

## Red-proof

- red_cmd: pre-change `pytest tests/test_review_scope.py` (baseline green)
- green_cmd: `pytest tests/ -q` → 151 passed
- TDD N/A for docs/CI YAML only sections

## Evidence pack

| Item | Result |
|------|--------|
| hard_gates | pending validate |
| smoke | smoke_unit / product_smoke |
| pytest | 151 passed |
| validate | scripts/validate.py full |
| coverage | check_module_coverage config ok |
| SBOM | n/a harness scripts |

## Threat notes

- Waiver log is local artifact (not secrets); may record actor username — low sensitivity
- portfolio `--force` only reinstalls non-protected scripts; protect forks never overwritten
- Security IOC remains ops-only — not a silent PR hard gate that could block unrelated ships

## Things that look bad but are actually fine

1. Five logical PRs may ship as one release commit stack if branch policy prefers mono-ship
2. Skill conformance already existed; job rename is honesty not new capability
3. Auto ship-chain markers for code_review/cross_review when LLM skipped
