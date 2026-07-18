# PR Draft — vault dev-log newest-first UTC+HKT

**Date:** 2026-07-18  
**Task:** Spec 2026-07-18-vault-dev-log-standard — prepend + dual zone + night_shift dedupe  
**Version target:** 1.3.2

## Summary

- `sync_vault_devlog.py`: newest-first **prepend**, `**When:** UTC · HKT`, `**Kind:** release|note`
- Night_shift notes: one per product per UTC day (marker without PASS/FAIL) unless `--force`
- Tests: `tests/test_sync_vault_devlog_format.py`
- Products reinstalled with same script; live agent-harness vault log updated

## Evidence

- pytest format tests + kanban tests green
- `validate.py full` 4/4
- Live prepend on `/opt/second-brain/vault/01-Projects/agent-harness/dev-log.md`

## Cross-review

**Marker:** CROSS-REVIEW  
**Blockers:** 0 · **Major:** 0 · **Nits:** 1

### Security Guru
- none — no secrets in log format; vault paths optional

### Maintainability Expert
- none — pure helpers unit-tested; append_entry aliases prepend
- nit — historical vault rows remain old order until rewritten

### Domain Specialist
- none — Option A release vs note preserved; products thin

### Obsolete / cleanup (scoped)
- Tier C: old append-order history in vault (migrate-on-write / optional normalizer later)

## Things that look bad but are actually fine

1. **History still chronological at bottom** — only new writes prepend; full reorder is out of scope for this ship.
2. **Night_shift skip same day** — intentional dedupe; use `--force` to override.
3. **HKT on entry when writer runs in UTC** — correct dual display for Obsidian operators.
4. **Product copies of one script** — install_into_product pattern; SoT remains harness git.
