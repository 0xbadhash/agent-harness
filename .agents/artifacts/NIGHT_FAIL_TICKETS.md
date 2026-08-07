# NIGHT_FAIL_TICKETS

_Updated 2026-08-07 13:53 UTC after readiness recheck._

Open after bounded autofix. Close when product readiness is green.

## Closed this cycle (were FAIL → now PASS)

- [x] agent-harness — validate_full + smoke green
- [x] catalyxt — validate_full + e2e smoke green
- [x] substack-push — hardcodes allowlist + validate green
- [x] watchlist — product_plugin mypy + coverage threshold normalize + smoke green

## Still open

## email-detach (FAIL)

- [ ] [email-detach] clear `validate_full` until night readiness PASS
  - evidence: morning_triage recheck still red (validate_full)
  - vault: `01-Projects/email-detach/TODO.md`
