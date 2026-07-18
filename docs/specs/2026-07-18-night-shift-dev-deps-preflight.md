# Night shift preflight: ensure Python dev deps per product

- **Product:** agent-harness (SoT for multi-product night_shift)
- **Created:** 2026-07-18
- **Status:** ready-for-agent
- **Priority:** P0
- **Roadmap:** `.agents/BACKLOG.md` / `CHANGELOG.md` Unreleased
- **Plan:** none (localized to orchestrator + optional small script)
- **Tracker:** local · meta item (2)
- **Constitution:** report-only night_shift; no auto-fix product logic

## Problem Statement

Multi-product night_shift often FAILs with `No module named pytest` / missing mypy/ruff because products use system `python3` without `.venv`. Operators re-debug the same env failure every night (03:15 HKT) instead of real product regressions.

## Solution

Before running each product’s `night_shift_readiness.py`, the orchestrator **preflights** Python tooling:

1. Prefer `product/.venv/bin/python` (already partially true via `_product_python`).  
2. If `requirements-dev.txt` or `pyproject` dev deps expected: ensure importable **pytest** (and optionally mypy/ruff when product uses them).  
3. If missing: attempt **non-destructive** install into product `.venv` when venv exists **or** create `.venv` + `pip install -r requirements-dev.txt` when that file exists.  
4. Record preflight result in multi-product report (PASS/SKIP/FAIL reason).  
5. Never `pip install` system-wide as root; never auto-fix product source.

### Recommended defaults

| Case | Behavior |
|------|----------|
| `.venv` exists, deps importable | SKIP install, run readiness |
| `.venv` exists, missing pytest | `venv/bin/pip install -r requirements-dev.txt` if file exists; else FAIL preflight with clear message |
| No `.venv`, `requirements-dev.txt` exists | `python3 -m venv .venv` then pip install (once) |
| No `.venv`, no requirements-dev | SKIP preflight install; use `_product_python` as today (may still fail gates — report clearly) |
| `ensure_dev_deps.py` present (e.g. substack-push) | Prefer running it after pip; must exit 0 |

## User Stories

1. As an **operator**, I wake to night_shift FAIL only for real gate failures, not missing pytest.  
2. As **night_shift**, I log “preflight: installed deps in .venv” once and continue.  
3. As a **security-conscious host**, I never get global `sudo pip install`.  

## Implementation Decisions

**Primary surface:** `bin/night_shift_all_products.py`  
**Optional helper:** `scripts/ensure_product_dev_env.py` (pure, unit-testable) called per product.  
**Per-product:** leave product `ensure_dev_deps.py` if present; do not require all products to have it.  
**Timeout:** pip install cap e.g. 600s; failure → product row FAIL with preflight tail.  
**Idempotent:** second run is no-op when imports work.  

### Non-goals

- Fixing product test logic  
- Installing Node deps (npm) in this ticket (optional follow-up for TS products)  
- Changing gate definitions  

## Testing Decisions

- Unit tests with tmp_path: mock product tree with/without venv and requirements-dev  
- Prove red: preflight function missing → test fails  
- Integration dry-run: one product path  
- Full harness pytest + product_smoke  

## Acceptance Criteria

- [ ] Multi-product runner preflights each registered product before readiness  
- [ ] Missing pytest with `requirements-dev.txt` triggers venv+pip (or documents SKIP if policy blocks create)  
- [ ] Preflight never uses `sudo pip` / system site-packages write  
- [ ] Multi SUMMARY or ALL report shows preflight notes for failures  
- [ ] Unit tests cover create-venv / skip-ok / fail-no-requirements cases  
- [ ] Harness pytest green; hardcode scan green  
- [ ] Docs: `docs/night-shift.md` one section “Dev env preflight”  
- [ ] night_shift hard-stops unchanged (no release/push/auto-fix product code)  

## Out of Scope

- Node `npm ci` preflight  
- Dockerized product envs  
- Migrating all products to poetry/uv  

## Clarifications

### 2026-07-18

- Q: Auto-create `.venv`?  
  - A: **Yes** when `requirements-dev.txt` exists (recommended default).  
- Q: Global COMPLIANCE_PYTHON fallback?  
  - A: Keep product `.venv` preferred; optional env override documented.  
- Q: npm for substack-push?  
  - A: Out of scope this ticket; note as P2.  

## Further Notes

Related: substack-push `scripts/ensure_dev_deps.py` is a model; harness should generalize lightly without copying product-specific tools.

## Handoff

- Next: `/execute_dev` in **agent-harness** (P0 Next)  
- Then: `/cross_review` if non-trivial → `/pr_review` → `/release_mgmt` → reinstall products  
