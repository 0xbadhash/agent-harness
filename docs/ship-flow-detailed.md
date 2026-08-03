# Detailed ship flow (harness) — skills, gates, TDD, soft vs hard

**Audience:** operators **and any LLM** running portable skills under `.agents/skills/`.  
**Scope:** **agent-harness SoT only** (product domain skills like Catalyxt news are out of band).  
**Diagrams:** Mermaid (GitHub-native) + overview poster ([SVG](diagrams/ship-flow-overview.svg) · [Draw.io](diagrams/ship-flow-overview.drawio)).

| Read this if… | Start here |
|---------------|------------|
| First time / any LLM | [llm-bootstrap.md](llm-bootstrap.md) then **this page top-to-bottom** |
| Phase / transition rules only | [ship-flow.md](ship-flow.md) |
| Per-skill “when to fire” | [skills-catalog.md](skills-catalog.md) |
| TDD discipline | [tdd.md](tdd.md) |
| Overnight readiness | [night-shift.md](night-shift.md) |

**Non-negotiable for LLMs**

1. Do **not** invent the next skill — run `python3 scripts/next_skill.py --after <skill>`.  
2. Do **not** hand-edit `pipeline.json` — only `scripts/pipeline_state.py`.  
3. **Hard gates fail closed** at `/pr_review --validate` (`hard_gates=25` all-or-nothing).  
4. **Five phases only:** `init` · `ready_for_review` · `approved` · `blocked` · `shipped`.

---

## 0. Overview poster

![Ship flow overview](diagrams/ship-flow-overview.svg)

- Editable source: [diagrams/ship-flow-overview.drawio](diagrams/ship-flow-overview.drawio) (open in [diagrams.net](https://app.diagrams.net/)).  
- Prefer **Mermaid sections below** for skill-level detail; poster is the mental model.

---

## 1. Phase FSM (hard states)

Phases live in `.agents/state/pipeline.json`. Only `pipeline_state.py` may change phase.

```mermaid
stateDiagram-v2
  [*] --> init
  init --> ready_for_review: /execute_dev\n(after implement + required reviews)
  ready_for_review --> approved: /pr_review --validate\nscore ≥ 95
  ready_for_review --> blocked: /pr_review --validate\nscore < 95
  blocked --> ready_for_review: /execute_dev\n(remediation only)
  approved --> shipped: /release_mgmt\n(+ smoke; infra if required)
  shipped --> init: /sync_docs
  note right of approved
    /vps_infra_ops --verify
    does NOT change phase
  end note
  note right of init
    /spec never changes phase
  end note
```

| From | To | Who may set | Hard gate (summary) |
|------|-----|-------------|---------------------|
| `init` | `ready_for_review` | `/execute_dev` | Task done; validate/smoke as needed; non-prose reviews done |
| `ready_for_review` | `approved` | `/pr_review --validate` | Score ≥ 95 (includes hard_gates) |
| `ready_for_review` | `blocked` | `/pr_review --validate` | Score &lt; 95 |
| `blocked` | `ready_for_review` | `/execute_dev` | Fix cited issues only |
| `approved` | `shipped` | `/release_mgmt` | product_smoke; tag/version |
| `shipped` | `init` | `/sync_docs` | Repo stamps |

**Illegal:** `/pr_review` from `init`; `/release_mgmt` before `approved`; inventing phases.

---

## 2. Happy-path skill sequence (on-phase)

Skills **inside** the FSM (order is enforced by `next_skill.py`, not by free choice).

```mermaid
flowchart TB
  subgraph INIT["Phase: init"]
    SPEC["/spec\nREQUIRED for features\nor Spec waiver"]
    EX["/execute_dev\nTDD + implement + validate"]
    SPEC --> EX
  end

  EX --> NS1{"next_skill\n--after execute_dev"}
  NS1 -->|prose-only| PR["/pr_review --validate"]
  NS1 -->|non-prose| CR["/code_review"]

  CR --> NS2{"next_skill\n--after code_review"}
  NS2 -->|large / force| XR["/cross_review"]
  NS2 -->|runtime| BV["/behavior_validator"]
  NS2 -->|small non-runtime| PR

  XR --> NS3{"next_skill\n--after cross_review"}
  NS3 -->|runtime| BV
  NS3 -->|else| PR

  BV --> PR

  PR --> SCORE{"score ≥ 95?"}
  SCORE -->|yes| APP["phase = approved"]
  SCORE -->|no| BLK["phase = blocked"]
  BLK --> EX

  APP --> INF{"infra required?"}
  INF -->|yes| VPS["/vps_infra_ops --verify\nphase stays approved"]
  INF -->|no| REL
  VPS --> REL["/release_mgmt"]
  REL --> SHP["phase = shipped"]
  SHP --> SYN["/sync_docs"]
  SYN --> INIT2["phase = init"]
  INIT2 --> QA{"large ship\nand not --skip-qa?"}
  QA -->|yes| QAC["/qa_campaign\noff-phase"]
  QA -->|no| DONE["NEXT_SKILL=(done)"]
```

---

## 3. NEXT_SKILL decision tree (after reviews)

```mermaid
flowchart TD
  A["--after execute_dev"] --> B{prose_only / skip_heavy?}
  B -->|yes| PR["/pr_review --validate"]
  B -->|no| CR["/code_review"]

  C["--after code_review"] --> D{large or --force-cross?}
  D -->|yes| XR["/cross_review"]
  D -->|no| E{runtime surface?}
  E -->|yes| BV["/behavior_validator"]
  E -->|no| PR

  F["--after cross_review"] --> G{runtime surface?}
  G -->|yes| BV
  G -->|no| PR

  H["--after behavior_validator"] --> PR
  I["--after pr_review"] --> J{infra required?}
  J -->|yes| VPS["/vps_infra_ops --verify"]
  J -->|no| REL["/release_mgmt"]
  VPS --> REL
  K["--after release_mgmt"] --> SYN["/sync_docs"]
  L["--after sync_docs"] --> M{large or --force-qa?}
  M -->|yes| QA["/qa_campaign"]
  M -->|no| D0["(done)"]
```

**Command (mandatory handoff line):**

```bash
python3 scripts/next_skill.py --after <skill_just_finished> --base <task-base> --head HEAD
# prints exactly one: NEXT_SKILL=…
```

---

## 4. TDD inside `/execute_dev`

See also [tdd.md](tdd.md). Code ships are **fail-closed on process honesty** via hard gate **Red-proof**.

```mermaid
sequenceDiagram
  participant A as Agent
  participant T as Test runner
  participant C as Code
  participant P as PR_DRAFT

  Note over A: Phase must be init or blocked
  A->>A: spec_gate.py (Spec path or waiver)
  A->>T: Red — add/extend failing tests
  T-->>A: MUST fail
  alt tests pass immediately
    A-->>A: OVER-SPECIFICATION — fix tests first
  end
  A->>C: Green — minimum implement
  A->>T: Green — tests pass
  A->>C: Refactor (stay green)
  A->>T: Regression + product smoke if runtime
  A->>P: red_cmd / green_cmd + Traceability + Evidence pack
  A->>A: pipeline_state → ready_for_review
  A->>A: next_skill --after execute_dev
```

| Case | Required evidence |
|------|-------------------|
| Behavior/code change | Red must fail, then green; document `red_cmd` / `green_cmd` |
| Docs-only / prose | `TDD N/A (docs-only)` or waiver; no silent skip of code work |

---

## 5. Hard vs soft gates

### 5.1 Hard (fail closed — ship stops)

| Gate | When | Enforced by | Artifact / check |
|------|------|-------------|------------------|
| Spec or Spec waiver | Always at score | `hard_gates.py` | `**Spec:**` path or `**Spec waiver:** hotfix\|chore\|docs-only\|prose-only` |
| CODE-REVIEW marker | Non-prose code ships | hard_gates | `.agents/artifacts/CODE_REVIEW.md` contains `CODE-REVIEW` |
| Red-proof | Non-prose | hard_gates | red_cmd/green_cmd or TDD N/A language in PR_DRAFT |
| Traceability | Non-prose | hard_gates | `## Traceability` AC → test/smoke |
| Evidence pack | Non-prose | hard_gates | `## Evidence pack` with ≥2 of hard_gates/smoke/pytest/validate/coverage/SBOM |
| BEHAVIOR-REPORT | Runtime surface | hard_gates | `.agents/artifacts/BEHAVIOR_REPORT.md` |
| Threat notes | Runtime surface | hard_gates | `## Threat notes` ≥2 bullets |
| Secrets on diff | Score | hard_gates + check_secrets_diff | Clean or fail |
| PR score ≥ 95 | `/pr_review --validate` | `pr_validator.py` | Rubric includes hard_gates=25 all-or-nothing |
| Phase preconditions | Every skill | skill text + pipeline_state | e.g. release only if `approved` |
| product_smoke | `/release_mgmt` | `product_smoke.py` | plugin `smoke[]` exit 0 |
| Spec gate pre-code | `/execute_dev` code | `spec_gate.py` | Spec path exists or waiver |

```mermaid
flowchart LR
  PR["/pr_review --validate"] --> HG["hard_gates.py"]
  HG -->|any violation| FAIL["hard_gates=0 → score fails\nphase → blocked"]
  HG -->|all pass| OK["hard_gates=25"]
  OK --> RUB["other rubric points"]
  RUB -->|total ≥ 95| APP["approved"]
  RUB -->|total < 95| BLK["blocked"]
```

### 5.2 Soft (skip, warn, or suggest — not score-kill by themselves)

| Mechanism | Behavior |
|-----------|----------|
| prose-only / skip_heavy_review | Skip code_review + cross_review + behavior path |
| cross_review | Only when large / forced; soft evidence warn unless `--strict-cross-review` |
| qa_campaign after sync_docs | Only large (or `--force-qa`); else `(done)` |
| vps_infra_ops | Only if product marks infra required |
| night_shift autofix | Mechanical once; residual → TODO |
| morning triage / remediate | Report + bounded fix; **no auto-ship of features** |
| portfolio_install | Default after **harness** release; products report lag |
| run_ship_chain | Deterministic closeout helper; not a substitute for LLM review quality |

### 5.3 Bounded automation (ops lane — not ship phases)

```mermaid
flowchart TB
  NS["night_shift-all.timer\n19:15 UTC"] --> R["readiness gates\nhardcodes / validate / smoke …"]
  R --> AF["autofix once\ndeps / format / ws"]
  AF --> R2["re-run gates"]
  R2 --> TODO["TODO + PROPOSE\nvault / artifacts"]
  TODO --> MT["morning_triage\n+ optional recheck"]
  MT --> REM["night_fail_remediate\nbounded + TICKETS"]
  REM --> HUM["Human / agent:\nfix product reds\nfull FSM if needed"]
```

---

## 6. Skills map (portable harness)

### 6.1 On-phase / ship chain (must follow NEXT_SKILL)

| Skill | Phase effect | Hard inputs |
|-------|--------------|-------------|
| `/spec` | none | Spec file + roadmap OPEN |
| `/execute_dev` | → ready_for_review | init\|blocked; TDD; validate |
| `/code_review` | none | CODE-REVIEW artifact |
| `/cross_review` | none | CROSS-REVIEW (large) |
| `/behavior_validator` | none | BEHAVIOR-REPORT (runtime) |
| `/pr_review` | → approved \| blocked | score ≥ 95 |
| `/vps_infra_ops` | none | INFRA_RUNBOOK if required |
| `/release_mgmt` | → shipped | smoke; tag; portfolio install if harness SoT |
| `/sync_docs` | → init | stamps |
| `/qa_campaign` | none | after full cycle when suggested |

### 6.2 Off-phase / support (do not invent as “next ship step”)

| Skill | Role |
|-------|------|
| `/night_shift` | Overnight readiness |
| `/retrospect` | Learning notes |
| `/feedback` | Session notes (harness meta) |
| `/handoff` / `/session_viewer` / `/agent_transcript` | Continuity / audit |
| `/plan_backend` / `/audit_repo` / `/sweep` / `/test_automation` | Support, not phase drivers |

Install manifest: `config/ship_skills.txt`.

---

## 7. Scripts LLMs must know

| Script | Role | Hard / soft |
|--------|------|-------------|
| `pipeline_state.py` | FSM get/set | Hard (only mutator) |
| `next_skill.py` | NEXT_SKILL= line | Hard routing contract |
| `spec_gate.py` | Spec before code execute | Hard for code |
| `hard_gates.py` | Evidence pack at score | Hard |
| `pr_validator.py` | Score + phase | Hard |
| `review_scope.py` | prose_only / large / baseline | Soft routing input |
| `product_smoke.py` | Plugin smoke | Hard on release |
| `validate.py` / compliance | Daytime quality | Soft/hard by product |
| `finish_ship.py` | Push proof checklist | Soft helper / hard with `--require-push` |
| `run_ship_chain.py` | Deterministic unattended closeout | Soft helper (no LLM reviews) |
| `night_shift_morning_triage.py` | Morning FAIL table | Ops |
| `night_fail_remediate.py` | Bounded autofix + tickets | Ops |
| `portfolio_install_report.py` | Product harness lag; `--install --push` | Default after harness tag |
| `remaining_board.py` | REMAINING.md | Soft memory |

---

## 8. Artifacts checklist (score-time)

| Artifact | Owner skill | Hard when |
|----------|-------------|-----------|
| `PR_DRAFT.md` | implementer | Always useful; Spec/waiver always hard |
| `.agents/artifacts/CODE_REVIEW.md` | code_review | Non-prose |
| `.agents/artifacts/CROSS_REVIEW.md` | cross_review | Large (soft unless strict) |
| `.agents/artifacts/BEHAVIOR_REPORT.md` | behavior_validator | Runtime |
| `RELEASE_RUNBOOK.md` | release_mgmt | Ship |
| `.agents/artifacts/PUSH_PROOF.md` | finish_ship | Closeout |
| `.agents/artifacts/REMAINING.md` | remaining_board | Operator memory |
| `.agents/artifacts/MORNING_TRIAGE.md` | morning triage | Ops |
| `.agents/artifacts/NIGHT_FAIL_TICKETS.md` | night_fail_remediate | Ops |

---

## 9. LLM operating loop (copy-paste)

```text
1. python3 scripts/pipeline_state.py get
2. If feature work and no Spec/waiver → /spec first
3. /execute_dev  (TDD if code; spec_gate)
4. python3 scripts/next_skill.py --after execute_dev --base <base> --head HEAD
5. Run exactly NEXT_SKILL=…  (repeat after each skill)
6. /pr_review --validate  when next says so  → approved | blocked
7. If blocked → /execute_dev remediation only → back to reviews
8. /release_mgmt when approved (+ infra if required)
9. /sync_docs → init
10. finish_ship / push; if this is agent-harness SoT → portfolio_install --install --push
```

**Deterministic shortcut (no LLM review depth):**

```bash
python3 scripts/run_ship_chain.py --root . --base <task-base> --head HEAD --push
```

Use for chore/closeout automation; **do not** use as an excuse to skip real review on product features.

---

## 10. Related docs

| Doc | Purpose |
|-----|---------|
| [ship-flow.md](ship-flow.md) | Canonical short FSM + ASCII map |
| [skills-catalog.md](skills-catalog.md) | Skill index |
| [llm-bootstrap.md](llm-bootstrap.md) | Any-LLM entry |
| [tdd.md](tdd.md) | Red→green |
| [night-shift.md](night-shift.md) | Overnight + morning |
| [start-a-feature.md](start-a-feature.md) | /spec front door |
| [security.md](security.md) | Secrets / threat posture |

---

## 11. Diagram maintenance

| Asset | Role | Edit with |
|-------|------|-----------|
| This file (Mermaid) | Detailed SoT for skills/gates | Text PR |
| [diagrams/ship-flow-overview.drawio](diagrams/ship-flow-overview.drawio) | Poster SoT | diagrams.net |
| [diagrams/ship-flow-overview.svg](diagrams/ship-flow-overview.svg) | GitHub/static render | Export from Draw.io after edit |

When changing phases or hard gates: update **this page + ship-flow.md + hard_gates.py behavior** in the same PR.
