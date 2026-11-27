---
name: prototype
description: >
  Disposable variants for a shape question. Generates two or three sketches, settles the choice in the grill, records the verdict, and deletes the directory before implementation. Use for /prototype, "which shape", "show me two options", or a design question in /spec.
disable-model-invocation: true
user-invocable: true
max-retries: 0
timeout-seconds: 300
---
# Reads: the grill question, `GLOSSARY.md` (when present), `.agents/decisions/`
# Writes: `.agents/prototypes/<slug>/variant-{a,b,c}.md`, a verdict in the spec
# Anti-patterns: policy/AGENT_REFERENCE.md

## What a prototype is

A prototype answers a **shape** question — "cache by ticker or by snapshot?",
"one screen or two?" — with two or three throwaway sketches. It is a reference,
never the implementation. Prototype code is deleted before the build starts; the
implementation copies the chosen shape, never the sketch text.

## Workflow

1. **Name the question.** One sentence, decision-shaped. If the answer would not
   change what we build, this is not a prototype question.
2. **Generate.**
   ```bash
   python3 scripts/prototype_variants.py new --slug <slug> \
     --question "Cache by ticker or by portfolio snapshot?" --variants 3
   ```
3. **Compare in the grill.** Walk the operator through the variants, one
   difference each. Ask which shape to keep and why.
4. **Record the verdict** in the spec:
   `**Prototype:** \`.agents/prototypes/<slug>\`` and
   `**Prototype verdict:** variant b — survives restart, less code`.
5. **Delete before implementation.**
   ```bash
   rm -rf .agents/prototypes/<slug>
   ```
   Update the verdict to say `deleted` if the directory is removed before the PR.
6. **Check fidelity before review.**
   ```bash
   python3 scripts/check_prototype_fidelity.py --root .
   ```
   Fails when the verdict is missing, a leftover variant lacks `DO NOT SHIP`, or
   prototype text appears in `scripts/`, `src/`, or another implementation area.

## Rules

- Do not build the feature from a prototype file. Re-implement the shape with
  tests; `check_prototype_fidelity.py` blocks a copied sketch.
- Do not keep prototypes "for reference" in the repo. The verdict plus the spec
  reasoning is the record.
- If the operator declines a prototype, write `**Prototype:** none` and move on.

## Handoff

```text
✅ PROTOTYPE VERDICT: <variant> — <one line why>
NEXT_SKILL=/spec (resume grill)
```
