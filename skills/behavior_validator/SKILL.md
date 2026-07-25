---
name: behavior_validator
description: >
  Source-blind validation of user/operator-visible behavior against a short
  behavior contract (apps, CLIs, APIs, generated artifacts). Pair with code_review;
  does not set pipeline phase.
disable-model-invocation: true
user-invocable: true
max-retries: 0
timeout-seconds: 900
preserve-artifacts-on-failure: true
---

# `/behavior_validator` — black-box behavior check (P1)

Companion to source-aware `/code_review` / `/cross_review`:

| Skill | Judges |
|-------|--------|
| code_review / cross_review | Diff / source |
| **behavior_validator** | Running product / CLI / API / artifact vs **contract** |

## When

- After `/code_review` or `/cross_review` when `next_skill.py` routes here (runtime surface)
- User asks to validate “as a user” without reading code
- After fixing a behavior finding (re-run affected clauses)

**Skip** when `NEXT_SKILL` is already `/pr_review` (no runtime surface) or user passes skip.

## Contract first

1. Load or write a short contract (see `references/contract-template.md`).
2. Prefer `.agents/artifacts/BEHAVIOR_CONTRACT.md` or path from user.
3. If missing, draft from the task + user stories, then validate against it.

## Rules

1. **Source-blind.** Do not open implementation files, diffs, or tests to decide pass/fail.
2. Interact only via user-visible surfaces: HTTP URL, CLI, API, generated files, public logs.
3. Each clause → `pass` | `fail` | `blocked` | `out_of_scope`.
4. Anti-cheat: empty/invalid input, retry, persistence, “fake success” UI.
5. Evidence: redacted notes only (no secrets).
6. Write `.agents/artifacts/BEHAVIOR_REPORT.md` (marker `BEHAVIOR-REPORT`).
7. **Do not** set `pipeline.json`.

## Commands

```bash
# What to run next after this skill:
python3 scripts/next_skill.py --after behavior_validator
# → NEXT_SKILL=/pr_review --validate
```

Prefer product smoke from `product_plugin.yaml` as one surface among others.

## Handoff

Always print:

```text
NEXT_SKILL=/pr_review --validate
```

(or run `scripts/next_skill.py --after behavior_validator`).
