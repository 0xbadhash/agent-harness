# CROSS-REVIEW — runner-label gate

**Marker:** CROSS-REVIEW
**Scope:** `origin/main...HEAD` (13 files, 729 non-test LOC)
**Secrets scan:** `python3 scripts/check_secrets_diff.py --base origin/main --head HEAD`
→ clean
**Blocker count:** 0

## Personas

1. **Security Guru.** The checker reads repository files and never executes
   them. It makes no network call, imports only `yaml`, and writes nothing. A
   `runs-on` expression is reported as unresolved instead of being expanded, so
   a crafted matrix value cannot hide an undeclared label. The workflow change
   keeps `permissions:` and `secrets.GITHUB_TOKEN`; it adds no secret.
2. **Maintainability Expert.** The parser lives in one module with a single
   entry point (`check`) and a thin CLI (`main`). Skip conditions are explicit
   and tested: no workflows, no allowlist, and empty allowlist. The
   workflow-harness side enforces the same contract from its own data instead of
   importing across repos.
3. **Operator / Release.** A failure names workflow, job, and label, which is
   the whole fix path. The gate is opt-in by adding the allowlist, so installing
   the new harness does not fail products that never adopted it. The reports are
   outside the repo and state their pinned commits.
4. **Test Quality.** Nine agent-harness tests cover pass, fail, both skips,
   empty allowlist, list-valued `runs-on`, expression, unparsable YAML, and
   `.yaml`. Three workflow-harness tests cover allowlist presence, declaration,
   and the exact label on both jobs.

## Obsolete / cleanup (scoped)

- No dead code, commented-out block, or ownerless TODO in the added lines
  (`check_comment_audit.py --diff origin/main...HEAD --strict` → clean).
- No duplicated parser: workflow-harness asserts its own data and does not copy
  the implementation.
- `docs/ci-matrix.md` gains a J17 row and a runner-label section; the row points
  at the script that exists.

## Findings

- **None.** No P0 or security-major finding survived verification.
- **Follow-up, out of scope:** the missing `GLOSSARY.md` (re-score item 1) makes
  two existing checks inert. Recorded in the re-score; not changed here.

## Evidence pack

- hard_gates: `python3 scripts/hard_gates.py --diff origin/main...HEAD` → pass
- pytest: `python3 -m pytest -q` → 636 passed, 2 skipped, 11 subtests
- validate: `python3 scripts/validate.py full` → 9/9 gates
- smoke: `python3 scripts/product_smoke.py --root .` → 2/2 steps
- workflow-harness: `python3 -m pytest tests -q --ignore=tests/enhancement_specs`
  → 226 passed

## Traceability

- AC-1/AC-2 → `tests/test_workflow_runners.py` (agent-harness)
- AC-3 → `scripts/hard_gates.py` registration; diff run output
- AC-4 → workflow-harness `tests/test_workflow_runners.py`
- AC-5 → `/srv/boxdrop/out/SCORECARD-GROKBUILD-HARNESS-TOP50-RESCORE-2026-11-28.md`
- AC-6 → `/srv/boxdrop/out/TRIAGE-PRS-2026-11-28.md`
