# HSQ-3 P3 — Protect-list SoT pin (warn)

**Version target:** 1.4.25  
**Date:** 2026-08-10

## Item G15

Warn when product `pipeline_state.py` / `hard_gates.py` diverge from harness SoT.
Default exit 0; `--strict` fails. Portfolio report notes SoT pin drift.

## AC

| ID | Criterion |
|----|-----------|
| AC-1 | Identical files → ok |
| AC-2 | Diverged pipeline_state → warn message lists path |
| AC-3 | `--strict` returns exit 1 on drift |
| AC-4 | portfolio_install_report notes include SoT pin drift when present |
