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
| `init` | Idle / cycle open; ready to implement | **`/spec` for features** (or Spec waiver), then `/execute_dev` |
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
| `init` (post-ship) | *(no phase)* | `/qa_campaign` | **Suggested** after full FSM (esp. large releases); does not change phase |

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
  │   /spec          REQUIRED for features (or Spec waiver)     │
  │                  phase stays init — hard gates need Spec    │
  │   /execute_dev   needs: init | blocked; runs spec_gate      │
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
  │        │                                                  │
  │        │  next_skill.py --after sync_docs                 │
  │        ▼                                                  │
  │   NEXT_SKILL=/qa_campaign   (optional deep QA; not a phase)│
  │   skip: --skip-qa → (done)                                │
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

0. `/spec` — **required for features** (or **Spec waiver** for hotfix/chore/docs-only/prose-only). Constitution + clarify; `.agents/specs/`; roadmap OPEN; **phase stays `init`** but score/spec_gate enforce Spec. See [start-a-feature.md](start-a-feature.md).  
1. `/execute_dev` — one task, TDD for code; needs `init` or `blocked`; runs `scripts/spec_gate.py`  

2. `next_skill.py --after execute_dev` → usually `NEXT_SKILL=/code_review`  
3. `/code_review` — required for non-prose; then `next_skill` again  
4. `/cross_review` and/or `/behavior_validator` — **only if** `NEXT_SKILL` says so  
5. Smoke / `validate` — behavior ≠ source  
6. `/pr_review --validate` — needs `ready_for_review`; score ≥ 95 → `approved`  
7. `/vps_infra_ops --verify` — **only if required** for this product; phase stays `approved`  
8. `/release_mgmt` — smoke from **product_plugin**, tag → `shipped`  
9. `/sync_docs` — docs + optional vault → `init`  
10. `/qa_campaign` — **optional** deep E2E QA + bug hunt after full FSM (suggested by `next_skill`; not a phase)  

**Always parse one line:** `NEXT_SKILL=/skill …`

### One-shot user phrase (any LLM)

```text
Full ship FSM for <task>:
/execute_dev then /code_review then (if NEXT_SKILL says) /cross_review
and/or /behavior_validator then /pr_review --validate
then (if required) /vps_infra_ops --verify then /release_mgmt
then /sync_docs then git push origin main --tags
then (optional, after huge release) /qa_campaign
```

See [llm-bootstrap.md](llm-bootstrap.md) for install + discovery.

### Side skills (not ship phases)

| Skill | When |
|-------|------|
| `/handoff` | Switch agent/session (P2) |
| `/session_viewer` | HTML view of a local session log (P3) |
| `/agent_transcript` | Sanitized transcript for PR body; ask user first (P3) |
| `/night_shift` | Overnight readiness; no phase advance — [night-shift.md](night-shift.md) |
| `/qa_campaign` | Post-FSM deep QA / bug hunt (orchestrated); no phase advance |
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
| `scripts/check_daytime_wiring.py` | A3: verify workflow + deploy units + product template present |
| `scripts/install_daytime_timer.sh` | A3: dry-run / `--apply` install of daytime-gates systemd timer |
| `deploy/daytime-gates.{service,timer}` | A3: multi-product daytime (18:00 UTC) |
| `templates/daytime-gates.yml` | A3: product-copy GHA workflow |
| `scripts/vault_fs.py` / `ensure_vault_group_write.py` | Vault group-write for night_shift logs |
| `scripts/session_viewer.py` | JSONL/text → HTML |
| `scripts/agent_transcript.py` | find/render sanitized markdown |
| `scripts/cross_review_gate.py` | Soft large-diff evidence warn |
| `scripts/pr_validator.py` | Deterministic score + pipeline phase |
| `scripts/pipeline_state.py` | FSM get/set phase |
| `scripts/finish_ship.py` | A1/A3: NEXT_SKILL plan + PUSH_PROOF (optional `--require-push`) |
| `scripts/promote_night_fails.py` | A5/A8: promote repeated FAIL gates → NIGHT_FAIL_PROMOTIONS |
| `scripts/portfolio_install_report.py` | A4: product HARNESS_VERSION residual; optional `--install`/`--push` |
| `scripts/remaining_board.py` | A2/B6: durable REMAINING.md (OPEN + night signals) |
| `scripts/night_shift_morning_triage.py` | Morning FAIL aggregate after night_shift |

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

## Hard gates pack (`pr_validator`)

`/pr_review --validate` awards **hard_gates = 25 points** only when **all applicable**
evidence checks pass (`scripts/hard_gates.py`). Fail closed → score cannot reach 95.

| Gate | When required | Evidence |
|------|---------------|----------|
| **Spec** | Always | `**Spec:** path` **or** `**Spec waiver:** …` in PR_DRAFT (also `spec_gate.py` / pipeline `spec_id`/`waiver`) |
| **CODE-REVIEW** | Non-prose ships | `.agents/artifacts/CODE_REVIEW.md` with marker `CODE-REVIEW` |
| **Red-proof** | Non-prose ships | `PR_DRAFT` has red_cmd/green_cmd / Red-proof / TDD N/A |
| **Traceability** | Non-prose ships | `## Traceability` mapping AC → test/smoke |
| **BEHAVIOR-REPORT** | Non-prose **and** runtime | `.agents/artifacts/BEHAVIOR_REPORT.md` |
| **Threat notes** | Non-prose **and** runtime | `## Threat notes` ≥2 bullets in PR_DRAFT |
| **Secrets** | Git work tree + diff | `check_secrets_diff` exit 0 |

Prose-only (`review_scope` skip_heavy_review): skips CODE-REVIEW, red-proof, traceability, behavior, threat.  
**B1:** `/execute_dev` runs `python3 scripts/spec_gate.py` before code work.  
Emergency: `pr_validator.py --skip-hard-gates`.

CLI:

```bash
python3 scripts/hard_gates.py --diff HEAD~1...HEAD
python3 scripts/pr_validator.py --diff HEAD~1...HEAD --update-pipeline
```

## Soft gates

- **Cross-review:** large diffs warn without evidence; optional `--strict-cross-review`  
  - Product paths come from `product_plugin.product_path_prefixes` (not hard-coded stack paths)
- **TDD process** in execute_dev (red before green) — **red-proof hard gate** records it for score
- **Smoke:** `python3 scripts/product_smoke.py` reads plugin smoke[] at release
- **PR score `suite_green`:** green type/lint/test suite only — **not** red-first proof (see hard Red-proof)

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
