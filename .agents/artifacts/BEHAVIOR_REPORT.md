# BEHAVIOR-REPORT — top-50 gap closure

**Marker:** BEHAVIOR-REPORT
**Contract:** `.agents/artifacts/BEHAVIOR_CONTRACT.md`
**Method:** source-blind CLI calls on temporary fixtures under `/tmp`; no source
was opened to decide a verdict.

| Clause | Verdict | Evidence |
|--------|---------|----------|
| B1 | pass | `ok: 29 glossary term(s) in glossary.md` exit 0; duplicate fixture: `'Door' collides with 'door'` exit 1 |
| B2 | pass | classify: `history: # previously returned None → delete`; constraints: unbounded exit 1, `test_run_first` exit 0 |
| B3 | pass | `ticket DAG valid (2 tickets); ready frontier: 01` exit 0 |
| B4 | pass | `✅ would merge 01 (PR ?)` and `02` |
| B5 | pass | missing reference exit 1 with the named failure; recorded reference skips |
| B6 | pass | `no run records; nothing to retro` exit 0 |
| B7 | pass | `2 smoke step(s) passed`; `9/9 gates passed` |

No clause is `fail`, `blocked`, or `out_of_scope`.
