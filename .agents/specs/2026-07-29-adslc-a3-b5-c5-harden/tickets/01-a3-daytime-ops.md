# Ticket 01 — A3 daytime ops wire-up

- **Spec:** `.agents/specs/2026-07-29-adslc-a3-b5-c5-harden.md`
- **Priority:** P0
- **Status:** open

## Acceptance

- [ ] deploy service + timer for multi-product daytime_readiness_subset
- [ ] install_daytime_timer.sh dry-run / --apply
- [ ] check_daytime_wiring.py + tests
- [ ] templates/daytime-gates.yml
- [ ] docs night-shift.md + ship-flow

## Out

- B5 / C5
- Force-enabling timer on this host without operator request at apply time
