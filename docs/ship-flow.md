# Ship flow

## Pipeline FSM (full)

**FSM** means **Finite State Machine**: a fixed set of **phases (states)** and allowed **transitions**. The ship pipeline is an FSM so agents cannot invent arbitrary “we’re done” paths — each skill only advances when the current phase and gates allow it.

| Term | Meaning here |
|------|----------------|
| **FSM** | Finite State Machine (not a product name or acronym for something else) |
| **Phase / state** | One of five: `init`, `ready_for_review`, `approved`, `blocked`, `shipped` |
| **Transition** | Moving to the next phase via `scripts/pipeline_state.py` only |
| **Gate** | Deterministic check before a transition (e.g. PR score ≥ 95, TDD evidence) |
| **Skill path** | Slash skills + `NEXT_SKILL=` (may run *inside* a phase without changing it) |

**State file (per product):** `.agents/state/pipeline.json`  
**Mutations:** `scripts/pipeline_state.py` only (atomic).  
**Inspect:** `python3 scripts/pipeline_state.py get`

Related (product vaults / second-brain kanban): a **card-level ship FSM** may use stages like `spec` → `execute_dev` → `cross_review` → `pr_review` → `release` → `sync_docs` → `done`. Same idea; product install SoT remains `pipeline.json` below.

---

### 1. States (complete set)

| State | Meaning | Typical next skill |
|-------|---------|-------------------|
| `init` | Idle / cycle open; ready to implement | `/spec` (optional), then `/execute_dev` |
| `ready_for_review` | Implement + required reviews done; scoring next | `/pr_review --validate` |
| `approved` | Score ≥ 95; may ship | `/vps_infra_ops --verify` **only if required**, then `/release_mgmt` |
| `blocked` | Score failed; remediation | `/execute_dev` (fix only cited issues) |
| `shipped` | Tagged / released | `/sync_docs` → back to `init` |

No other phase strings are valid.

---

### 2. Allowed phase transitions

```text
                    ┌──────────────────────────────┐
                    │                              │
                    ▼                              │
                 ┌──────┐                          │
            ┌───►│ init │◄──────────────────┐      │
            │    └──┬───┘                   │      │
            │       │ /execute_dev          │      │
            │       │ (after implement +    │      │
            │       │  required reviews)    │ /sync_docs
            │       ▼                       │      │
            │  ┌─────────────────┐          │      │
            │  │ ready_for_review│          │      │
            │  └────────┬────────┘          │      │
            │           │                   │      │
            │           │ /pr_review --validate    │
            │     ┌─────┴─────┐             │      │
            │     ▼           ▼             │      │
            │ ┌────────┐  ┌─────────┐       │      │
            │ │approved│  │ blocked │───────┼──────┘
            │ └───┬────┘  └────┬────┘  fix  │
            │     │            │ /execute_dev
            │     │            └────────────┘
            │     │  if infra required:
            │     │    /vps_infra_ops --verify
            │     │    (phase stays approved)
            │     │  then /release_mgmt
            │     ▼
            │ ┌─────────┐
            └─┤ shipped │
              └─────────┘
```

| From | To | Skill that may set it | Gate (summary) |
|------|-----|----------------------|----------------|
| `init` | `ready_for_review` | `/execute_dev` | Task done; validate green; reviews required for non-prose |
| `ready_for_review` | `approved` | `/pr_review --validate` | Score ≥ 95 |
| `ready_for_review` | `blocked` | `/pr_review --validate` | Score &lt; 95 |
| `blocked` | `ready_for_review` | `/execute_dev` | Remediation only; re-validate |
| `approved` | *(no phase change)* | `/vps_infra_ops --verify` | **Only when infra is required** (see below); writes `INFRA_RUNBOOK.md` |
| `approved` | `shipped` | `/release_mgmt` | Smoke OK; version/tag; fresh infra PASS if required |
| `shipped` | `init` | `/sync_docs` | Repo (and optional vault) stamps |

**Illegal (must halt with `🛑 WRONG STATE`):** e.g. `/pr_review` from `init`, `/release_mgmt` from `ready_for_review`, `/sync_docs` advancing without `shipped`, inventing phases, hand-editing `pipeline.json` outside `pipeline_state.py`.

**Does not change phase:** `/spec`, `/code_review`, `/cross_review`, `/behavior_validator`, **`/vps_infra_ops`**, `/handoff`, `/session_viewer`, `/agent_transcript`, `/night_shift`.

---

### 3. Full map — skills inside the phase FSM

Routing after `/execute_dev` / `/code_review` / `/cross_review` / `/behavior_validator`:

```bash
python3 scripts/next_skill.py --after <skill> [--base <ref> --head HEAD]
# → exactly one line: NEXT_SKILL=/…
```

Do **not** invent the next slash skill.

```text
══════════════════════════════════════════════════════════════════
  FULL SHIP FSM  ·  phases (pipeline.json) + skills (NEXT_SKILL)
══════════════════════════════════════════════════════════════════

  ┌─ STATE: init ─────────────────────────────────────────────┐
  │                                                             │
  │   /spec          optional; phase stays init                 │
  │   /execute_dev   needs: init | blocked                      │
  │        │                                                    │
  │        ▼                                                    │
  │   [implement + TDD + validate + smoke as needed]            │
  │        │                                                    │
  │        │  next_skill.py --after execute_dev                 │
  │        │                                                    │
  │        ├─ prose-only ──► NEXT_SKILL=/pr_review --validate   │
  │        │                 (skip heavy code_review)           │
  │        │                                                    │
  │        └─ non-prose ──► NEXT_SKILL=/code_review             │
  │                              │                              │
  │                              ▼                              │
  │                    /code_review  (required closeout)        │
  │                    · P0-first · secrets · CODE_REVIEW.md    │
  │                    · does NOT set phase                     │
  │                              │                              │
  │              next_skill.py --after code_review              │
  │                              │                              │
  │              ┌───────────────┼───────────────┐              │
  │              ▼               ▼               ▼              │
  │        large/non-triv.   runtime surface   small code       │
  │              │               │               │              │
  │              ▼               ▼               │              │
  │       /cross_review   /behavior_validator    │              │
  │       (personas)      (source-blind)         │              │
  │              │               │               │              │
  │              │    next_skill after each      │              │
  │              │               │               │              │
  │              └───────┬───────┴───────────────┘              │
  │                      ▼                                      │
  │         NEXT_SKILL=/pr_review --validate                    │
  │                      │                                      │
  │   /execute_dev sets phase ──► ready_for_review              │
  │   (when implement + required reviews are done;              │
  │    same session OK)                                         │
  └──────────────────────┼──────────────────────────────────────┘
                         │
                         ▼
  ┌─ STATE: ready_for_review ─────────────────────────────────┐
  │                                                             │
  │   /pr_review --validate   ← ONLY skill → approved|blocked   │
  │        │                                                    │
  │        ├─ score ≥ 95 ──► approved                           │
  │        └─ score < 95 ──► blocked                            │
  └───────────┬─────────────────────┬───────────────────────────┘
              │                     │
              ▼                     ▼
  ┌─ approved ──────────┐   ┌─ blocked ───────────────────────┐
  │                     │   │                                   │
  │  if infra required: │   │  /execute_dev  (remediation)      │
  │    NEXT_SKILL=      │   │  → reviews → ready_for_review     │
  │    /vps_infra_ops   │   │  → /pr_review again               │
  │    --verify         │   └───────────────────────────────────┘
  │  · INFRA_RUNBOOK    │
  │  · phase stays      │
  │    approved         │
  │  else: skip infra   │
  │        │            │
  │        ▼            │
  │  NEXT_SKILL=        │
  │  /release_mgmt      │
  │  · smoke · VERSION  │
  │  · tag · phase →    │
  │    shipped          │
  └─────────┬───────────┘
            │
            ▼
  ┌─ STATE: shipped ──────────────────────────────────────────┐
  │   /sync_docs  →  stamps + optional vault → phase init     │
  └───────────────────────────────────────────────────────────┘
```

---

### 4. Branch / gate notes

| Branch or gate | Meaning |
|----------------|---------|
| **prose-only** | `review_scope` `skip_heavy_review` — internal notes/skill prose; may skip heavy `/code_review` + `/cross_review`; still score at `/pr_review` |
| **large / non-trivial** | Shared heuristic in `review_scope.is_large_baseline`: files ≥ 8, or churn ≥ 200, or non-test LOC ≥ 150, or ≥ 3 product_path_prefixes hits → `/cross_review` after `/code_review` (same thresholds as `cross_review_gate`) |
| **runtime surface** | Code/config that can affect a running product → `/behavior_validator` before score |
| **score ≥ 95** | `scripts/pr_validator.py` rubric (suite, gates, §9, hardcodes, hygiene) |
| **blocked** | Fix in-scope only; re-enter via `/execute_dev` from `blocked` |
| **`/vps_infra_ops` (conditional)** | Named product infra skill. **Triggered / suggested only when required** (below). Does **not** change phase. After PASS → `NEXT_SKILL=/release_mgmt`. |

#### When is `/vps_infra_ops` required / suggested?

**Suggest and run** `/vps_infra_ops --verify` after `approved` **only if** at least one of:

1. Product has the skill: `.agents/skills/vps_infra_ops/SKILL.md` (or product-owned equivalent), **or**
2. `product_plugin.yaml` sets infra required (e.g. `infra.required: true` / `require_vps_infra: true`), **or**
3. `/release_mgmt` / product policy demands a fresh **INFRA VERIFIED** runbook (≤24h) before tag.

**Skip** (go straight to `/release_mgmt`) when:

- Product has **no** vps/infra skill and no infra gate, **or**
- Operator / `next_skill` path explicitly skips infra, **or**
- Valid `INFRA_RUNBOOK.md` already PASS within window and policy allows reuse.

Router (when approved after pr_review):

```bash
python3 scripts/next_skill.py --after pr_review
# → NEXT_SKILL=/vps_infra_ops --verify   # only if infra required for this product
# → NEXT_SKILL=/release_mgmt             # otherwise

python3 scripts/next_skill.py --after vps_infra_ops
# → NEXT_SKILL=/release_mgmt
```

**Off-FSM skills (never advance `pipeline.json`):** `/handoff`, `/session_viewer`, `/agent_transcript`, `/night_shift`, `/audit_*`, etc.

---

### 5. Phase ownership (who may transition)

| Phase | Who advances | Skill |
|-------|--------------|--------|
| → `ready_for_review` | implementer | `/execute_dev` |
| → `approved` / `blocked` | reviewer | `/pr_review --validate` |
| → `shipped` | releaser | `/release_mgmt` |
| → `init` (close cycle) | docs | `/sync_docs` |

---

### 6. Recommended order (same path, numbered)

0. `/spec` — constitution + interview + **clarify**; `.agents/specs/` (+ optional plan/tickets); roadmap OPEN; **phase stays `init`**  
1. `/execute_dev` — one task, TDD for code; needs `init` or `blocked`  
2. `next_skill.py --after execute_dev` → usually `NEXT_SKILL=/code_review`  
3. `/code_review` — required for non-prose; then `next_skill` again  
4. `/cross_review` and/or `/behavior_validator` — **only if** `NEXT_SKILL` says so  
5. Smoke / `validate` — behavior ≠ source  
6. `/pr_review --validate` — needs `ready_for_review`; score ≥ 95 → `approved`  
7. `/vps_infra_ops --verify` — **only if required** for this product; phase stays `approved`  
8. `/release_mgmt` — smoke from **product_plugin**, tag → `shipped`  
9. `/sync_docs` — docs + optional vault → `init`  

**Always parse one line:** `NEXT_SKILL=/skill …`

### One-shot user phrase (any LLM)

```text
Full ship FSM for <task>:
/execute_dev then /code_review then (if NEXT_SKILL says) /cross_review
and/or /behavior_validator then /pr_review --validate
then (if required) /vps_infra_ops --verify then /release_mgmt
then /sync_docs then git push origin main --tags
```

See [llm-bootstrap.md](llm-bootstrap.md) for install + discovery.

### Side skills (not ship phases)

| Skill | When |
|-------|------|
| `/handoff` | Switch agent/session (P2) |
| `/session_viewer` | HTML view of a local session log (P3) |
| `/agent_transcript` | Sanitized transcript for PR body; ask user first (P3) |
| `/night_shift` | Overnight readiness; no phase advance — [night-shift.md](night-shift.md) |
| `/sweep` / `/audit_*` | Hygiene / gap analysis |

Full catalog: [skills-catalog.md](skills-catalog.md).

### Review / ops helpers (scripts)

| Script | Role |
|--------|------|
| `scripts/next_skill.py` | **Single-line handoff** `NEXT_SKILL=…` after each step |
| `scripts/review_scope.py` | Baseline files/LOC; `prose_only` / `skip_heavy_review` |
| `scripts/check_secrets_diff.py` | Diff-scoped secret scan (gitleaks/trufflehog or regex) |
| `scripts/check_hardcodes.py` | Paths/URLs/secrets scan (content/vendored trees skipped) |
| `scripts/smoke_unit.sh` | Portable unit smoke (prefer over nested `bash -c`) |
| `scripts/daytime_readiness_subset.py` | Daytime hardcodes + validate + smoke (pre-night) |
| `scripts/vault_fs.py` / `ensure_vault_group_write.py` | Vault group-write for night_shift logs |
| `scripts/session_viewer.py` | JSONL/text → HTML |
| `scripts/agent_transcript.py` | find/render sanitized markdown |
| `scripts/cross_review_gate.py` | Soft large-diff evidence warn |
| `scripts/pr_validator.py` | Deterministic score + pipeline phase |
| `scripts/pipeline_state.py` | FSM get/set phase |

## PR_DRAFT narrative (template)

Implementers fill `PR_DRAFT.md` from `templates/PR_DRAFT.md` before `/pr_review`:

| Section | Intent |
|---------|--------|
| **What Problem This Solves** | Pain / bug / gap before the change |
| **Why This Change Was Made** | Rationale and rejected alternatives |
| **User Impact** | Who notices (operator, agent, ops, none) |
| **Evidence** | Tests, live smoke, validator — how we know it works |
| Red-proof / Cross-review / §9 | Existing process gates |

## Artifacts

| Artifact | Owner |
|----------|--------|
| `PR_DRAFT.md` | pr_review / implementer |
| `.agents/artifacts/CROSS_REVIEW.md` | cross_review |
| `.agents/artifacts/CODE_REVIEW.md` | code_review (optional) |
| `.agents/artifacts/INFRA_RUNBOOK.md` | `/vps_infra_ops --verify` (when required) |
| `RELEASE_RUNBOOK.md` | release_mgmt |
| Vault release block | sync_docs (`sync_vault_devlog.py` without `--note`) — shape: **[dev-log.md](dev-log.md)** |
| Vault ad-hoc note | any task (`--note`; never `synced` in title) — same Option A standard |

## Validate gates (`validate.py full`)

| Gate | When |
|------|------|
| compliance_engine (type/lint/test) | full / compliance |
| check_hardcodes | full / hygiene |
| check_repo_hygiene | full / hygiene |
| check_module_coverage | full / hygiene |
| **check_dev_log_contract** | full / hygiene **if vault present** (this product’s `01-Projects/<label>/dev-log.md`) |

See `docs/dev-log.md`. Overnight multi-product job still normalizes + checks **all** logs.

## Soft gates

- **Cross-review:** large diffs warn without evidence; optional `--strict-cross-review`  
  - Product paths come from `product_plugin.product_path_prefixes` (not hard-coded stack paths)
- **TDD:** process gate in execute_dev (red must fail before green)
- **Smoke:** `python3 scripts/product_smoke.py` reads plugin smoke[] at release
- **PR score `suite_green`:** green type/lint/test suite only — **not** red-first proof

## Off-pipeline: night readiness (`/night_shift`)

**Not** a ship FSM phase. Overnight (or on-demand) **readiness** so the next `/execute_dev` can start on green surfaces.

- Does **not** advance `pipeline.json`  
- Does **not** release or tag  
- Writes reports + optional vault TODO only  

Full ops doc: **[night-shift.md](night-shift.md)**.

## Related

- [TDD](tdd.md)  
- [Night shift](night-shift.md)  
- [Skills catalog](skills-catalog.md)  
