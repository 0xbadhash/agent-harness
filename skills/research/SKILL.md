---
name: research
description: >
  Cited, offline-usable research report. Turn a question and source notes into
  a markdown artifact where every claim carries a citation. Use before a spec
  when the decision depends on outside facts.
disable-model-invocation: true
user-invocable: true
max-retries: 0
timeout-seconds: 600
---

# `/research` — cited repo artifacts (E24)

Research that cannot be re-checked is folklore. This skill produces a markdown
artifact in the repo with a source for every claim.

## Contract

1. Write the question and the decision it informs at the top.
2. For each claim, record a source: a path in this repo, a URL, or a dated
   document. A claim without a source is a **note**, and notes do not decide.
3. Prefer primary sources. If two sources disagree, say so and keep both.
4. Mark confidence (`high` / `medium` / `low`) and the reason.
5. Output `docs/research/<date>-<slug>.md` via `scripts/research_report.py`.
6. Never paste secrets, tokens, private URLs, or raw personal data.
7. When the research changes a decision, link the artifact from the spec.

## Workflow

```bash
# notes.md: headings = claims, each followed by "Source: ..."
python3 scripts/research_report.py \
  --question "Which queue gives at-least-once delivery here?" \
  --notes notes.md \
  --out docs/research/2026-11-22-queue-choice.md --strict
```

`--strict` fails when a claim has no source. The report is a repo artifact: it
is reviewed with the spec and can be cited in the PR body.

## When not to use

- The answer is already in the repo: cite the file and skip the report.
- The question is a preference with no external facts: use the grill instead.
