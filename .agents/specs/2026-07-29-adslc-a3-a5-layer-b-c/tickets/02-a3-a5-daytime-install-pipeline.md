# Ticket 02 — A3 Daytime CI + A4 Install delete/stamp + A5 Pipeline identity (P0)

**Status:** open  
**Blocked by:** none (can parallelize after 01 if needed)  
**Spec:** `.agents/specs/2026-07-29-adslc-a3-a5-layer-b-c.md`

## Goal

Wire daytime readiness for CI/cron; install drops stale portable skills and stamps version; pipeline.json carries spec_id/card_id/waiver.

## Acceptance

- [ ] Example GH Actions workflow for daytime_readiness_subset  
- [ ] night-shift.md cron snippet  
- [ ] install `--delete-stale-skills` + `HARNESS_VERSION`  
- [ ] pipeline_state extra fields + tests  
- [ ] product-only skills never deleted  

## Smoke

`bash install_into_product.sh … --verify --delete-stale-skills`; `pipeline_state.py get`
