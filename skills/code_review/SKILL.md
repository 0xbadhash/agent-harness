---
name: code_review
description: >
  Closeout code review of a git diff (required after execute_dev for non-prose
  code ships; skip only when review_scope says prose-only). Complements
  cross_review + pr_review; does not set pipeline phase.
disable-model-invocation: true
user-invocable: true
max-retries: 0
timeout-seconds: 900
preserve-artifacts-on-failure: true
---

# `/code_review` — closeout code review (optional)

**Not** a replacement for `/cross_review` (personas + obsolete scan) or
`/pr_review --validate` (deterministic score + FSM phase).

**When (mandatory from `/execute_dev`):** after implement + validate on any ship
whose `review_scope` is **not** prose-only. The implementer agent must invoke
this skill (or an equivalent structured pass that writes `CODE-REVIEW`) before
declaring `ready_for_review`.

Also use when:

- User asks for second-model / autoreview-style pass
- After fixing review findings (re-run once)

**Skip only** (prose-only exception): entire diff is internal notes / skill prose under
`.agents/skills/**/SKILL.md` or non-user-facing markdown — run
`python3 scripts/review_scope.py` to confirm `skip_heavy_review=true`, then
lightweight read of the diff only and record skip in handoff.

## Contract

1. **P0-first.** Default report only **blockers** (material break of normal flow,
   outcome, or safety). Include majors only for concrete security. Nits only if
   user asks `--wide` / P1+.
2. **Advisory.** Never blindly apply findings. Verify each against real code.
3. **Scope governor** (freeze baseline first):

   ```bash
   python3 scripts/review_scope.py --base origin/main --head HEAD --json
   ```

   Classify each finding before patching:

   | Class | Meaning |
   |-------|---------|
   | **in_scope_blocker** | Introduced by this diff, same owner boundary, fixable without new public contract |
   | **follow_up** | Real but adjacent / pre-existing / broader hardening |
   | **stop_and_escalate** | New API/protocol/migration/release-process or different owner |

   Stop after **two** review→fix cycles that do not converge; reclassify.
   If files or non-test LOC grow past **2×** baseline without approval → stop.

4. **Secrets on the bundle:**

   ```bash
   python3 scripts/check_secrets_diff.py --base <base> --head HEAD
   ```

   Fail closed on findings. Prefer gitleaks/trufflehog when installed.

5. **Engine.** Prefer a **different model** than the implementer when available:

   - Env: `CODE_REVIEW_MODEL` or `GROK_MODEL_CROSS_REVIEW` / product equivalent
   - Do not switch engines mid-run except documented access fallbacks

6. **Re-review.** If you change code for an accepted finding, re-run focused
   tests and this skill **once**. Stop when no accepted P0 remain.

7. **Behavior ≠ source.** Clean code review is **not** proof the product works.
   Always pair with product smoke / `validate full` before `/pr_review`.

8. **Do not** advance `pipeline.json`. That is `/pr_review --validate` only.

## Report artifact

Write `.agents/artifacts/CODE_REVIEW.md` (marker `CODE-REVIEW`) with:

- command / base / head
- secrets scan result
- findings accepted / rejected (brief why)
- P0 count; follow-ups listed separately
- smoke/tests run

## Handoff

```text
✅ CODE-REVIEW DONE  p0=N  follow_ups=M
   next: /cross_review (if not done) → /pr_review --validate
```
