# Product constitution (example)

Copy to the **product** repo as `.agents/CONSTITUTION.md` and edit.
`/spec` reads this before interviewing (Spec Kit–style principles, harness-native path).

## Purpose

What this product is for, in one paragraph.

## Non-negotiables

1. Prefer simple, reversible changes over clever ones.
2. Checkable acceptance criteria before implementation.
3. TDD (or explicit TDD N/A + smoke) for behavior changes — see `/execute_dev`.
4. No secrets in the repository.
5. Stay within product stack declared in `product_plugin.yaml`.

## Quality bar

- Smoke commands in `product_plugin.yaml` must pass before ship.
- User-visible changes preserve accessibility and (if present) dark mode.
- Large diffs get multi-persona review before score.

## Scope discipline

- One `/execute_dev` sub-task at a time.
- Specs state Out of Scope explicitly.
- Prefer vertical tickets over horizontal “layer” tickets.

## Security & privacy

- Least privilege for tools and integrations.
- Never log or commit credentials.

## How agents use this file

Read at the start of `/spec`, `/execute_dev`, and `/pr_review`.  
If a proposed change conflicts with this constitution, stop and ask the human.
