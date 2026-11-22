# Skill drift manifest (T2058U)

Canonical tree is `skills/`. `.agents/skills/` is the generated install copy.
Measured 2026-11-20: worktree `skills/` against the live install tree
`~/agent-harness/.agents/skills/` (read-only). Eight skills were byte-identical.
Eleven differed. `retrospect` is source-only. `challenge` is install-only.

Apply these lines in the merge commit. Do not delete a line marked `merge`.
The sweep `audit_repo` sentence is the only `listed deletion`.

| Skill | Line | Disposition |
|-------|------|-------------|
| code_review | `model: none` | merge |
| pr_review | `model: none` | merge |
| release_mgmt | `model: none` | merge |
| sync_docs | `model: none` | merge |
| spec | `model: grok-4.7` | merge |
| spec | `reasoning_effort: high` | merge |
| execute_dev | `model: grok-4.7` | merge |
| execute_dev | `reasoning_effort: high` | merge |
| execute_dev | `Else harness: first open row in `.agents/BACKLOG.md`.` | merge |
| agent_transcript | `always ask user before inserting` | merge |
| agent_transcript | `fail closed on secrets` | merge |
| session_viewer | `Ops/debug only — not a ship FSM step.` | merge |
| sweep | `Diff-scoped dead code only → /cross_review. Policy/gap framing → /audit_repo.` | listed deletion |
| audit_harness | (no installed-only line; source is strictly newer) | source wins |
| night_shift | (no unique constraint; see note) | source wins |
| challenge | `python3 scripts/challenge.py --proposal path/to/proposal.md` | merge |
| challenge | `python3 ~/agent-harness/scripts/challenge.py --proposal path/to/proposal.md --root <product-root>` | merge |
| challenge | `python3 scripts/challenge.py --proposal path/to/proposal.md --decision path/to/decision.md` | merge |
| challenge | GLM `z-ai-glm-5-3-flash` via `ask_glm.py` and Deepseek `deepseek-v4-flash` via Venice | merge |

## Notes

`agent_transcript` source already says "fail closed on secrets" and the body says "Always ask". The merge keeps the exact installed phrase `always ask user before inserting` in the source description. Older installed headings are not constraints.

`session_viewer` source already says "Not a ship FSM step." The merge keeps the installed constraint sentence in the description.

`sweep`: drop the installed pointer at `/audit_repo`. That name is in `config/removed_portable_skills.txt`. Source already points policy-gap narrative at `/audit_harness`.

`night_shift`: the live install copy's only line that is not in source is the short bullet `- Install: ./install_into_product.sh /path/to/product`. Source contains that command and adds the sibling-copy ban. Printed diff (install → source) shows additions only, plus that one extended bullet. It is not a unique constraint sentence. Source wins. The item did not stop.

`challenge`: start from the tracked 60-line `.agents/skills/challenge/SKILL.md` and add the four lines from the untracked dirty `~/agent-harness/skills/challenge/SKILL.md`. Do not edit either file under `~/agent-harness`.

`retrospect` stays in `skills/` and in `config/optional_skills.txt`. The generator copies it. It is not deleted.
