# PR Draft — night shift stops writing agent-tasks/kanban.md

**Spec waiver:** chore  
**Version target:** 1.4.36  

## What Problem This Solves
Night shift readiness still upserted vault `agent-tasks/kanban.md` Done notes every PASS (last hit T-NS-zk-business-card-20260819). Ops will delete the file; writers must stop first.

## Why This Change Was Made
CEO: night shift must not write kanban.md. Fail-closed ship on harness SoT only. Do not reopen 1.4.35 trait gates.

## User Impact
- `night_shift_readiness.write_vault` no longer touches kanban.md
- `upsert_kanban_readiness_done` / `sync_kanban_readiness_file` are no-ops (never write)
- Ops deletes kanban.md separately after this tag

## Red-proof
- red_cmd: `python3 -c "import importlib.util; from pathlib import Path; p=Path('scripts/night_shift_readiness.py'); s=importlib.util.spec_from_file_location('n', p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); t='KEEP'; o,_=m.upsert_kanban_readiness_done(t, product_id='x', overall='PASS', when_iso='2026-08-19T00:00:00Z', gate_summary='1/1'); import sys; sys.exit(0 if o!=t else 1)"`
- green_cmd: `python3 -m unittest tests.test_night_shift_kanban_sync -v`

## Traceability
| AC | Test / smoke |
|----|--------------|
| AC-1 upsert never mutates kanban text | tests/test_night_shift_kanban_sync.py::test_upsert_is_noop_unchanged |
| AC-2 sync never writes existing kanban.md | tests/test_night_shift_kanban_sync.py::test_sync_never_writes_kanban_file |
| AC-3 sync does not create missing kanban.md | tests/test_night_shift_kanban_sync.py::test_sync_does_not_create_missing_kanban |
| AC-4 write_vault does not touch kanban.md | tests/test_night_shift_kanban_sync.py::test_write_vault_does_not_touch_kanban |
| smoke | python3 -m unittest tests.test_night_shift_kanban_sync -v |

## Threat notes
- authz: vault writes still limited to project night-shift-log / TODO / optional devlog
- secrets: none logged by this change
- abuse: no recreate of agent-tasks/kanban.md

## Evidence pack
| Item | Result |
|------|--------|
| hard_gates | pr_validator |
| unittest | tests/test_night_shift_kanban_sync.py |
| red/green | red expects old mutate behavior EXIT 1; green unittest |

## Things that look bad but are actually fine
1. No portfolio install / product VERSION bumps
2. Dirty leftover MORNING_TRIAGE / NIGHT_SHIFT_* / ops_dashboard.py left unstaged
3. Night-bar 73c2221 stays unpushed
4. Does not reopen 1.4.35 trait-checklist PASSes
