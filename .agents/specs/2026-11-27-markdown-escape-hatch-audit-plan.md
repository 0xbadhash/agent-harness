# Plan — markdown escape-hatch audit

**Spec:** `.agents/specs/2026-11-27-markdown-escape-hatch-audit.md`

## Approach

Extend the existing comment audit with one class and one ratchet, add a sibling
Markdown checker that owns the `AGENTS.md` cap and the `## Do not` enforcement
rule, and wire both into the two local gates. Keep the checks dependency-free and
follow the `(ok, messages)` contract.

## Architecture

- `scripts/check_comment_audit.py` adds `escape_hatch`, `CHECK_REF_RE`, and a
  per-`path::kind` baseline so whole-tree runs ratchet.
- `scripts/check_markdown_audit.py` owns `check_agents_bloat` and `check`; it
  prefers harness `skills/` over installed `.agents/skills`.
- `scripts/check_stale_agent_config.py` calls `check_agents_bloat`.
- `scripts/hard_gates.py` adds `markdown_audit`; `scripts/validate.py` runs the
  baseline comment audit and the Markdown audit.
- `scripts/check_repo_hygiene.py` fails on `[DEBUG-…]` tags, matching the skill.

## Implementation sequence

1. Write the comment, Markdown, hygiene, and `hard_gates` tests.
2. Extend the comment audit and add the Markdown module; wire both gates.
3. Update the three `## Do not` sections, record the baseline, and verify.

## Risks and rollback

- Risk: the whole-tree audit fails on legacy comments. Mitigation: baseline file;
  delete the baseline gate call to roll back.
- Risk: installed `.agents/skills` copies drift from `skills/`. Mitigation: the
  scanner reads the SoT tree only; `install_into_product.sh` refreshes copies.
- Risk: false positives on table rows. Mitigation: only bullets and numbered
  rules are scanned.
