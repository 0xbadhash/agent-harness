# Spec: 50-enhancement batch — agent-harness (E01–E25)

Date: 2026-11-22 · Mode: batch spec per harness-fsm-ship "Spec-test suite BEFORE a batch implementation". Sources: forensic read of this repo (2026-11-22), Matt Pocock 21k-line-feature transcript + github.com/mattpocock/skills catalog, Lauren Tan SpaceXSI talk.

## Problem Statement
The harness enforces gates on products it does not apply to itself; gate
conventions are copy-pasted across 28 scripts; missing tools read as green
skips; fork drift is silent; review/PR/retro layers from the source talks
(smallest-visual PRs, two-axis review, ratcheting, retros, prototypes,
research, wizards) do not exist.

## Solution
Implement enhancements E01–E25 exactly as specified by the deterministic
acceptance suite `tests/enhancement_specs/test_agent_harness_e01_e25.py`
(one test per enhancement, red = pending). Each test asserts the END state
and must turn green WITHOUT EDITS when its enhancement lands.

## Implementation Decisions
- Single source of gate conventions: new `scripts/gate_conventions.py`
  exposing the Spec/waiver patterns; every gate script imports it; no inline
  `**Spec waiver:**` regex remains outside that module.
- Night shift: missing required tool (per-product manifest) ⇒ `DEGRADED`
  verdict; a suite that did not run ⇒ distinct `RED_SUITE` status, never skip.
- `bin/night_shift_all_products.py` is split into a library module under
  `scripts/` plus a thin CLI (≤400 lines).
- New gates: `check_pr_body.py` (smallest-visual summary, before/after
  evidence, one-way/two-way merge-danger call), comment audit, retro job
  (`retro_job.py`), fork sync bot (`fork_sync_bot.py`), compact-safety
  (`check_compact_safety.py`), prototype variants, wizard generator,
  research skill, ratcheting lint with a per-rule violation-count baseline
  data file that a checker consumes.
- `github_daytime_status.py` gains local↔origin parity with escalation.
- Spec gate additions: ADR three-part test (reversible/surprise/tradeoff),
  GLOSSARY enforcement, ticket blocking edges (`depends_on`), diff-sizing
  decision tree (small/medium/huge) in `start_feature.py`, repro
  requirement for bug fixes.
- cross_review_gate: separate standards and spec-fidelity axes.
- Smart-zone guard: ~150k token budget for implementer subagents with
  externalization past the budget.
- CI: daytime-gates.yml runs coverage via check_module_coverage.

## Testing Decisions
- The acceptance suite in `tests/enhancement_specs/` is deterministic
  (filesystem/AST/text, offline). It is the gate: an enhancement is done only
  when its test is green.
- Existing repo gates stay green; no gate script behavior changes beyond the
  additions above.

## Acceptance Criteria
- [ ] All 25 tests in tests/enhancement_specs/test_agent_harness_e01_e25.py green
- [ ] Repo's own gates (daytime suite) still pass
- [ ] No network/LLM in the new tests; suite runs <5s
- [ ] Work committed on branch `enh/50-spec-tests` (spec + tests + implementation)

## Grill-me (settled from on-disk facts)
- Where do the duplicated patterns live? 28 scripts currently inline
  `**Spec waiver:`; the canonical extraction target is `scripts/gate_conventions.py`.
- Is night_shift_all_products.py at scripts/? No — `bin/night_shift_all_products.py`.
- Does hypothesis exist in requirements-dev.txt? No — must be added.
- Protected paths: `.grok/`, profile scripts, vault — out of scope.
