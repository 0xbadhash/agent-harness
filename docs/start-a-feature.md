# Start a feature (operator front door)

**For code work, `/spec` is required** (or an explicit **Spec waiver**).  
It is **not** optional anymore: hard gates + `spec_gate.py` block `/pr_review` and expect a Spec path or waiver before/during ship.

**Grill-me is mandatory inside `/spec`.** The agent asks you questions (one at a time, with a recommended answer) before locking acceptance. Prefer answering over shipping the wrong product/feature. Evidence lives in the Spec under `## Grill-me` and is fail-closed via `scripts/check_spec_grill.py`.

Phase still stays `init` during `/spec` (spec does not advance the FSM). “Required” means **required for a clean code ship**, not “a pipeline phase.”

---

## What to type

| Work type | You write |
|-----------|-----------|
| **New feature / non-trivial change** | `/spec <outcome + scope>` then answer grill-me → `/execute_dev` |
| **Hotfix** | `/execute_dev …` with `**Spec waiver:** hotfix` in `PR_DRAFT` (or scaffold below) |
| **Chore / docs-only** | `**Spec waiver:** chore` or `docs-only` / `prose-only` |
| **True spike only** | `/spec --spike …` (must document **Reason** ≥20 chars under Grill-me) |

### Feature (recommended)

```text
/spec Users can <outcome>. In scope: …. Out of scope: ….
```

The agent will **grill-me** (G1–G7 themes) before finalize.  
Optional: `--plan`, `--tickets`, `--from-conversation`.  
**Not available:** `--no-interview` / `--no-clarify` (retired).

### Scaffold (files without full interview)

```bash
# Creates/updates PR_DRAFT with Spec + Traceability stubs
python3 scripts/start_feature.py --slug my-feature --title "Short title"

# Also write a draft spec stub
python3 scripts/start_feature.py --slug my-feature --write-spec-stub

# Hotfix path
python3 scripts/start_feature.py --slug fix-login --waiver hotfix --title "Fix login"
```

Then refine acceptance (or run `/spec` on the stub) and:

```text
/execute_dev
```

Follow every `NEXT_SKILL=` line through `/code_review` → … → `/pr_review --validate` → `/release_mgmt` → `/sync_docs`.

---

## Hard gates you must satisfy (code ships)

| Gate | Where |
|------|--------|
| **Spec** or **Spec waiver** | `PR_DRAFT.md` and/or `pipeline_state --spec-id` / `--waiver` |
| **Red-proof** | `PR_DRAFT` (`red_cmd` / `green_cmd` or TDD N/A) |
| **## Traceability** | AC → test/smoke table |
| **CODE-REVIEW** | `.agents/artifacts/CODE_REVIEW.md` |
| **BEHAVIOR-REPORT** | if runtime surface |
| **## Threat notes** | ≥2 bullets if runtime |

Check:

```bash
python3 scripts/spec_gate.py --root .
python3 scripts/hard_gates.py --diff HEAD~1...HEAD
```

---

## Related

- [ship-flow.md](ship-flow.md) — full FSM + hard gates  
- [llm-bootstrap.md](llm-bootstrap.md) — any LLM  
- [skills-catalog.md](skills-catalog.md) — when each skill fires  
