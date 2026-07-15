# Clarify checklist (`/spec` step 5)

Run **after** a draft spec, **before** `ready-for-agent`.  
Goal: “unit tests for English” — coverage of underspecified areas.

## Scan for gaps

Mark each as OK or needs Q:

| Area | Question if weak |
|------|------------------|
| Actor / user | Who is this for, and when do they care? |
| Happy path | What is the single primary success story? |
| Edge cases | Empty state, errors, partial failure? |
| Non-goals | What must we **not** build? |
| Permissions / secrets | Any auth, env, or PII? |
| Data | Create/read/update/delete? Retention? |
| UX / a11y | Keyboard, dark mode, mobile? |
| Verify | Smoke + manual path explicit? |
| Rollback | How do we undo a bad ship? |
| Dependencies | Blocked on credentials, third parties, other tickets? |
| Constitution | Conflicts with project principles? |

## Rules

1. Ask **one** question at a time.  
2. Prefer recommended answers from product context.  
3. Record Q/A under `## Clarifications` in the **spec** file.  
4. Patch acceptance criteria when answers change the definition of done.  
5. Stop when every acceptance line is objectively checkable.  
6. Cap ~8 questions unless the user invites more; leftover → Out of Scope or Open questions in plan.

## Anti-patterns

- Re-asking facts already in the repo or constitution  
- Stack debates during clarify (defer to `--plan`)  
- Clarifying forever without writing acceptance updates  
