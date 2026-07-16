# Obsolete / cleanup scan (shared protocol)

**Default mode: evidence only — no deletes, no `git rm`, no force-push.**  
Remediation requires explicit user OK (or a follow-up `/execute_dev` task with AC).

Used by:

| Skill | Scope | Where to put findings |
|-------|--------|------------------------|
| `/sweep` | **Whole repo** (product tree; skip vendor/node_modules/.venv) | Sweep report + optional worksheet; §9 noisies |
| `/cross_review` | **Review scope only** (uncommitted diff, `--diff A..B`, or named paths) — Maintainability persona | `## Cross-review` → obsolete subsection; severity map below |
| `/audit_repo` | **Whole repo** policy scan | `PRODUCTION_GAP_ANALYSIS.md` as GAP/DOC/OPS; false friends in §9 |

Do **not** treat this protocol as a pipeline phase advance.

---

## Goal

Find assets that are **obsolete, redundant, or useless**, with:

1. **Confidence** ∈ `[0, 1]` where **1 = highest** confidence it is safe/no product dependency.
2. **Evidence facts** (paths, `rg`/`git ls-files` results, test/doc/runtime refs) — not vibes.
3. Explicit **keep** list for things that look dead but are wired (scaffolds, gates, dual stacks).

---

## Method (minimum bar)

Run enough of the following to support each claim (adapt to product layout via `product_plugin.yaml` / `docs/PRODUCT.md`):

1. **Tracked cruft** — `git ls-files` vs `.gitignore` (e.g. `__pycache__`, `*.pyc`, `graphify-out/` if ignored).
2. **Orphan candidates** — root/diagnostic scripts, re-export-only tests, mocks, spike docs; count inbound refs (`rg`, pytest, bin entrypoints, nginx, docs).
3. **Stale comments** — “stub”, “later PRs”, “PR1”, “TODO remove” on code that is already implemented.
4. **False-positive guards** — if a path is named in pytest scaffolds, `bin/*`, product hub, `docs/PRODUCT.md`, or deploy units → confidence of “delete” must be **≤ 0.2** unless user redefines product boundary.
5. **Web exposure** (optional when applicable) — root `test_*.php` / debug scripts not denied by nginx while product is web-served.

Skip or one-line: pure vendor, generated bundles that are intentionally regenerated (`ALL_PRINCIPLES.md` via `build_principles`), local-only gitignored graphs.

---

## Output format (required)

### Confidence scale

| Score | Meaning |
|------:|---------|
| **0.9–1.0** | Doc-only rot, ignore-but-tracked noise, or pure re-export with zero external refs |
| **0.6–0.89** | Optional diagnostic / design artifact; removable after small ref updates |
| **0.3–0.59** | Unclear; needs product decision |
| **0.0–0.29** | **Keep** — product, gate, or intentional stub |

### Tables

1. **Tier A (high conf, low blast)** — conf ≥ 0.9  
2. **Tier B (medium)** — optional cleanup with listed ref updates  
3. **Tier C (looks dead, keep)** — conf of “is obsolete” low; evidence why it stays  

Each row: **Item | Conf | Verdict | Evidence** (1–3 concrete facts).

### Rules

- **No deletes** in the skill run that only “scans.”
- Recommend ordered cleanup only as a **proposal** list.
- Map severity for cross_review when something in-scope is dangerous (e.g. web-exposed debug + keys) → Security may also flag; Maintainability owns “dead/redundant.”
- Include **≥3** §9 “looks bad but fine” when the skill already requires §9 (sweep, cross_review, audit_repo).

### Severity map (cross_review only)

| Cleanup finding | Severity |
|-----------------|----------|
| Tracked secrets/debug that leak keys if hit | **blocker** (prefer Security) |
| Dead code paths that break maintainability of the **diff** | **major** |
| Stale comments, re-export tests, doc rot | **nit** |
| Whole-repo cruft outside review scope | mention once as “out of scope — run `/sweep`” — do not expand full repo table unless user asked |

---

## Copy-paste header for reports

```markdown
## Obsolete / cleanup scan (evidence only — no deletes)

**Scope:** {whole-repo | diff: <range> | paths: …}
**Skill:** {/sweep | /cross_review | /audit_repo}
**Protocol:** `.agents/policy/OBSOLETE_CLEANUP_SCAN.md`
```
