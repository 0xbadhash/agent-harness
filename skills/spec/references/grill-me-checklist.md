# Grill-me checklist (`/spec` — **mandatory** by default)

Run **before** status `ready-for-agent`.  
Goal: kill bad product/feature ideas early by **asking the operator** — never invent acceptance to “be helpful.”

Inspired by adversarial “grill the idea” practice (see `provenance.md`). This is **not** optional polish.

## Rules

1. **One question at a time.** Recommended answer every time.
2. Prefer **decisions only** — do not re-ask facts already in the repo or constitution.
3. Record every Q/A under `## Grill-me` in the **spec** file (required section).
4. If a grill answer **kills** the idea → status `rejected` or fold into Out of Scope; **do not** write tickets or plan for dead work.
5. If the operator says “you decide” → apply the **recommended** default and still **log** it under Grill-me (so the decision is auditably theirs via silence).
6. Cap: cover **all required themes** below (at least one Q per theme that is still open). Soft max ~12 questions total unless the operator invites more.
7. **Never skip grill-me** for feature ships. Only `--spike` (or Spec waiver path outside this skill) may omit — and must say so in the spec.

## Required themes (must address or mark N/A with reason)

| # | Theme | Grill question patterns (pick one that still open) |
|---|--------|-----------------------------------------------------|
| G1 | **Outcome** | What does “done” look like in one sentence a user would say? |
| G2 | **Non-goal / kill** | What must we **not** build? What would make you cancel this? |
| G3 | **Wrong product** | Could this be the wrong product surface / wrong repo / wrong user? |
| G4 | **Cheapest alternative** | What’s the smallest ship that still proves value (or docs/config only)? |
| G5 | **Abuse / failure** | How does this fail, get misused, or create support load? |
| G6 | **Verify** | How do we prove it in smoke/manual before merge? |
| G7 | **Priority / delay** | Why now vs next week? What happens if we ship nothing? |

## Recommended defaults (when operator is silent)

| Theme | Default |
|-------|---------|
| G2 Non-goal | No multi-agent runtime; no new product unless named |
| G4 Cheapest | Single vertical slice + existing smoke |
| G5 Abuse | Fail closed on secrets; no silent data loss |
| G6 Verify | Product `smoke[]` + one manual path from AC |
| G7 Priority | P1 unless user said P0/hotfix |

## Spec evidence shape

```markdown
## Grill-me

**Status:** complete | spike-skipped
**Date:** <ISO date>

### G1 Outcome
- Q: …?
  - A: …
  - Recommended was: …

### G2 Non-goal / kill
- Q: …?
  - A: …

… (G3–G7 as needed; mark N/A only with reason)
```

## Halt

| Halt | When |
|------|------|
| `🛑 GRILL MISSING` | Spec would be `ready-for-agent` without `## Grill-me` + at least **3** answered themes (or spike-skipped with reason) |
| `🛑 GRILL REJECTED` | Operator cancelled idea in grill — do not implement |

## P0 features — operator stays in the loop

For **P0** (wrong-product risk, security, money, irreversible data):

1. Prefer the **human operator** answers G1–G3 (outcome, non-goal/kill, wrong product).  
2. Do **not** accept “you decide” on those themes for P0.  
3. No extra heavy automated gate — process + existing grill evidence.  
4. See `docs/outer-loop-playbook.md` §5.

## Anti-patterns

- Drafting full AC without any grill Q/A  
- “Interview optional” or skipping because the agent is confident  
- Stack debates during grill (defer to `--plan`)  
- Rubber-stamp grill with empty “A: ok” lines  
- Agent inventing P0 grill answers unattended 
