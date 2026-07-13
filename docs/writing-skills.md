# Writing great skills

Style: **small, composable, failure-mode-driven** (Agent Skills format + progressive disclosure).

## Minimal `SKILL.md`

```markdown
---
name: my-skill
description: >
  One line: what it does + when to use it + when NOT to use it.
  Keywords the agent can match.
disable-model-invocation: true
user-invocable: true
---
# Reads: …
# Writes: …
# Anti-patterns: policy/AGENT_REFERENCE.md

When invoked:
1. …
2. …
```

## Rules of thumb

1. **One skill, one job.** If it exceeds ~two pages, split it.  
2. **Description is the API.** Front-load triggers; agents decide load from that.  
3. **Steps are non-negotiable.** Prefer checklists over essays.  
4. **Link depth.** Put long reference material in `docs/` and point to it.  
5. **No product stack.** Do not hard-code languages, frameworks, or hosts. Read `product_plugin.yaml` or say “use product smoke.”  
6. **Stateless first.** Prefer no cross-session files; add state only when proven necessary.  
7. **Fail closed.** Explicit halt strings (`WRONG STATE`, `SPEC MISSING`) beat silent improvisation.

## Where skills live

| Kind | Location |
|------|----------|
| Portable | this repo `skills/` |
| Product-only | product `.agents/skills/<name>/` |

After editing portable skills, tag a harness release and re-run `install_into_product.sh` in products.

## Security

Never instruct agents to curl untrusted scripts or read secrets into chat.  
See [security.md](security.md).

## Related

- [Skills catalog](skills-catalog.md)  
- [Overview](overview.md)  
