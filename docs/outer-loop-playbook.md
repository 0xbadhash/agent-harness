# Outer-loop playbook (host + harness)

**Audience:** operators and agents on this VPS portfolio.  
**SoT gates:** `scripts/check_outer_loop.py` (wired into `hard_gates`).  
**Related:** [start-a-feature.md](start-a-feature.md) · [skills-catalog.md](skills-catalog.md) · grill-me in `/spec`.

---

## 1. When to use what

| Situation | Do this | Do **not** |
|-----------|---------|------------|
| Hotfix / chore / docs-only | Spec **waiver** + short ship chain | Full grill + plan theater |
| Small feature (below large thresholds) | `/spec` with **grill-me** → implement | Invent multi-PR stacks |
| **Large** non-waiver ship | Grill → **Spec + Plan** → **PLAN_REVIEW** → tickets if steps ≥ N → execute | Jump to code after grill only |
| Ambiguous multi-week / multi-PR product bet | Host **`/design`** (writer↔reviewer) then **`/execute-plan`** stack; **each leaf PR** still runs harness ship | Multi-agent runtime inside agent-harness (NON_GOAL) |
| P0 product feature with wrong-product risk | **You stay in grill** (answer every theme); do not leave Q/A to the agent alone | Unattended “complete” grill with invented answers |

**Large** = `review_scope` thresholds (files / lines / non-test LOC / product paths). Override: `OUTER_LOOP_FORCE_PLAN=1`.

---

## 2. Host design / stack (multi-PR)

Use when the unit of value is **several PRs**, not one ship cycle:

```text
1. /design          → design doc + PR Plan DAG (host skill)
2. /execute-plan    → worktrees / stack (optional Graphite)
3. For each leaf PR:
     /spec (link design) → grill if new AC → plan if large
     → /execute_dev → reviews → /pr_review --validate → merge
4. Night bar still owns overnight truth (full smoke)
```

Harness does **not** own multi-agent orchestration. Host design answers *what stack of PRs*; harness answers *each PR is fail-closed*.

---

## 3. Fail-closed outer loop (harness)

For **large non-waiver** ships:

| Gate | Requirement |
|------|-------------|
| **Plan** | `**Plan:** path` to a real `-plan.md` with Approach/Architecture/Implementation sequence |
| **Tickets** | If Implementation sequence has **≥ N steps** (default **4**, env `OUTER_LOOP_TICKET_STEPS`), `**Tickets:**` dir with ≥1 ticket |
| **PLAN_REVIEW** | `.agents/artifacts/PLAN_REVIEW.md` with marker `PLAN-REVIEW`, ≥160 chars, verdict language |

Emergency: `OUTER_LOOP_SKIP=1` (prefer not).

---

## 4. Pre-code plan review (until/while plan gate is real)

After plan is written, **before** `/execute_dev` on large ships:

1. Open the plan file.  
2. Adversarial pass (product / security / ops): wrong surface? cheapest alternative? abuse?  
3. Write `PLAN_REVIEW.md` with **Verdict: PASS|FAIL** and ≥2 findings or explicit “no issues + why.”  
4. Only then implement.

This is intentional friction: plan gate without review becomes empty files.

---

## 5. P0 grill — operator stays in the loop

For **P0** features (wrong product / security / money path):

- Prefer answering grill questions **yourself** (one at a time is fine).  
- Do **not** tell the agent “you decide” on G1–G3 (outcome, non-goal, wrong product).  
- No extra heavy gate: trust process + existing grill evidence structure.  
- Spikes: `/spec --spike` with honest Reason only.

---

## 6. Defaults

| Knob | Default |
|------|---------|
| Ticket step threshold N | 4 |
| Force plan always | off (`OUTER_LOOP_FORCE_PLAN`) |
| Plan review min body | 160 chars |

---

## 7. Checklist (large feature)

- [ ] Grill-me complete (you answered P0 themes)  
- [ ] Spec ready-for-agent  
- [ ] Plan written (`/spec --plan`)  
- [ ] PLAN_REVIEW written  
- [ ] Tickets if sequence ≥ N  
- [ ] `/execute_dev` … `/pr_review --validate`  
- [ ] Night bar after merge  
