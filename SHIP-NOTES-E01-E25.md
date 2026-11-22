# SHIP NOTES — E01–E25

Branch: `enh/50-spec-tests` · Spec: `.agents/specs/2026-11-22-fifty-enhancements.md`
Acceptance gate: `tests/enhancement_specs/test_agent_harness_e01_e25.py` (frozen)

**Proof:** `.venv/bin/pytest tests/enhancement_specs -q` → `25 passed`.

| E | What was implemented | Files touched | Proving test |
|---|----------------------|---------------|--------------|
| E01 | Canonical Spec/waiver patterns in one module; every gate script imports it; no inline `**Spec waiver:**` regex remains outside the module. | `scripts/gate_conventions.py`; `spec_gate.py`, `hard_gates.py`, `check_waiver_budget.py`, `check_spec_hash.py`, `check_spec_grill.py`, `check_ac_traceability.py`, `check_changed_path_tests.py`, `check_outer_loop.py`, `run_ship_chain.py`, `start_feature.py` | `test_e01_gate_conventions_single_source` |
| E02 | CI runs the unit suite with `--cov` and enforces `check_module_coverage.py`; `pytest-cov` added to dev requirements. | `.github/workflows/daytime-gates.yml`, `requirements-dev.txt` | `test_e02_coverage_in_ci` |
| E03 | Daytime status compares local `main` to `origin/main` (`git rev-list --left-right --count`), renders a parity section, emits a 🚨 alert, and supports `--fail-on-drift`. | `scripts/github_daytime_status.py` | `test_e03_fork_drift_alarm` |
| E04 | Ship chain exposes an explicit `--self` path that runs the harness's own gates (`check_harness_manifest`, `check_daytime_wiring`) as `self:*` steps. | `scripts/run_ship_chain.py` | `test_e04_dogfood_ship_chain` |
| E05 | Per-product required-tools manifest; a missing required tool returns `DEGRADED` and `overall_verdict` ranks it above FAIL/RED_SUITE. | `scripts/night_shift_readiness.py` | `test_e05_missing_tool_is_degraded` |
| E06 | A suite that did not run gets the distinct `RED_SUITE` status; the missing-checker matrix path returns it instead of a silent skip. | `scripts/night_shift_readiness.py` | `test_e06_red_suite_status` |
| E07 | Orchestrator split into `scripts/night_shift_all_lib.py` plus a thin `bin/night_shift_all_products.py` CLI (113 lines), preserving patch seams (`run_one`, `collect_learn`, `subprocess.run`). | `bin/night_shift_all_products.py`, `scripts/night_shift_all_lib.py` | `test_e07_night_shift_split` |
| E08 | Hypothesis property tests for the gate parsers; dev dependency added. The module uses `pytest.importorskip` so an offline checkout without the wheel skips locally and CI runs it. | `tests/test_gate_parsers_property.py`, `requirements-dev.txt` | `test_e08_property_tests_for_parsers` |
| E09 | PR-body gate requires the smallest slice, before/after evidence, and an explicit one-way/two-way merge-danger call; ship chain can require it with `--require-pr-body`. | `scripts/check_pr_body.py`, `scripts/run_ship_chain.py` | `test_e09_pr_body_gate` |
| E10 | Cross review runs two axes: standards (bare `except`, ownerless TODO) and spec fidelity (each `AC-n` traced to the diff or tests); CLI `--axis`. | `scripts/cross_review_gate.py` | `test_e10_two_axis_review` |
| E11 | Per-rule lint violation counts checked in; the checker fails only when a rule rises above its baseline and supports `--update` to lower the ratchet. CI consumes it. | `config/lint_ratchet_baseline.json`, `scripts/check_lint_ratchet.py`, `.github/workflows/daytime-gates.yml` | `test_e11_ratcheting_lint` |
| E12 | Offline post-ship retro clusters review findings, transcripts, and waiver reasons into one ratchet proposal per cluster and writes `docs/retros/<date>-retro.md`. | `scripts/retro_job.py` | `test_e12_retro_job` |
| E13 | Spec gate tests the ADR three-part contract (reversibility, surprise, tradeoff) whenever the spec carries a decision record. | `scripts/spec_gate.py` | `test_e13_adr_three_part_test` |
| E14 | Spec gate resolves uppercase domain terms against `GLOSSARY.md` / `docs/GLOSSARY.md` when a glossary exists. | `scripts/spec_gate.py` | `test_e14_glossary_enforced` |
| E15 | Comment audit flags history comments, commented-out code, and TODOs without an owner or issue link; supports paths/diff/strict. | `scripts/check_comment_audit.py` | `test_e15_comment_audit_gate` |
| E16 | Tickets declare blocking edges (`**depends_on:**` / `**Blocked by:**`); the gate resolves targets, rejects dangling edges, self-blocks, and cycles. The generated ticket stub carries the edge line. | `scripts/spec_gate.py`, `scripts/start_feature.py` | `test_e16_ticket_blocking_edges` |
| E17 | Window open classifies planned work as small/medium/huge with a split-before-opening rule. | `scripts/start_feature.py` | `test_e17_diff_sizing_tree` |
| E18 | Smart-zone guard encodes the 150,000-token budget and emits an externalization plan (decisions, open questions, spec/tickets, fresh context). | `scripts/smart_zone_guard.py` | `test_e18_smart_zone_guard` |
| E19 | Compact-safety gate blocks compaction until the linked spec exists, at least one ticket is on disk, and a glossary is present. | `scripts/check_compact_safety.py` | `test_e19_compact_safety_gate` |
| E20 | Bug-fix specs must carry a `## Reproduction` naming the repro and the red result observed before the fix. | `scripts/spec_gate.py`, `scripts/check_red_green_cmds.py` | `test_e20_repro_required_for_bugfixes` |
| E21 | Waiver report clusters rows by `(gate, waiver_type)`, warns at three or more, and the spec gate records the gate name in the ledger. | `scripts/waiver_report.py`, `scripts/spec_gate.py` | `test_e21_waiver_clustering` |
| E22 | Prototype generator writes 2–3 lensed, `DO NOT SHIP` sketches per design question; the grill warns when a design question has no prototype note. | `scripts/prototype_variants.py`, `scripts/check_spec_grill.py` | `test_e22_prototype_variants` |
| E23 | Wizard generator writes human-only runbooks with owner, preconditions, numbered steps, verification, rollback, and handoff. | `scripts/wizard.py` | `test_e23_wizard_generator` |
| E24 | Research skill plus report generator: every bullet claim needs a `Source:` line or inline link; `--strict` refuses uncited claims; output lands in `docs/research/`. | `skills/research/SKILL.md`, `scripts/research_report.py` | `test_e24_research_skill` |
| E25 | Fork-sync bot compares local and origin refs and prepares a tracker issue with ahead/behind evidence and repair steps; files it only with `--create`. | `scripts/fork_sync_bot.py` | `test_e25_fork_sync_bot` |

## Supporting tests

`tests/test_enhancement_mechanisms.py` adds 27 behavior tests for the same
mechanisms (PR-body rejection, ratchet increase, two-axis findings, retro
clustering, comment classification, smart-zone boundary, compact-safety
block/pass, prototype lenses, wizard sections, cited research, fork divergence
parsing and issue creation, waiver clusters, DEGRADED/RED_SUITE precedence,
repro enforcement, and ticket cycles).

## Verification notes

- Determinism: the acceptance suite uses filesystem/text checks only, makes no
  network or LLM calls, and finishes in under one second.
- Hypothesis is declared in `requirements-dev.txt` but the wheel is absent from
  this offline environment, so `tests/test_gate_parsers_property.py` skips
  locally (`1 skipped`). CI installs the dev requirements and runs it.
- `scripts/check_compact_safety.py` correctly blocks compaction on this repo
  today because there is no root `GLOSSARY.md`. It is a new gate and is not yet
  wired into CI, so no existing behavior changes.
- Pre-existing worktree dirt was left uncommitted: `.agents/artifacts/*`,
  `.gitignore`, `CHANGELOG.md`, `PR_DRAFT.md`, `config/optional_skills.txt`,
  `scripts/challenge.py`, `scripts/ops_dashboard.py`,
  `scripts/watchlist_golden_drift.py`, their tests, and backup/untracked files.
- The full repo suite has one pre-existing failure,
  `tests/test_check_hardcodes_skips.py::test_real_src_url_still_flagged`, caused
  by that prior-effort uncommitted edit to `scripts/check_hardcodes.py` and its
  test. This batch does not touch either file.
