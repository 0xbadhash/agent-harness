# Coding conventions (agent index)

**Meta.** Product coding conventions: root `CODING_CONVENTIONS.md` + `docs/PRODUCT.md`.

| Concern | File |
|---------|------|
| Product vs agents | `docs/PRODUCT_BOUNDARY.md` |
| Harness home | `.agents/README.md` |
| Session phases | `.agents/AGENT_WORKFLOW.md` |
| Policy / TDD | `ENGINEERING_ASSURANCE.md` |
| Routing | `GEMINI.md` |
| PHP product layout | `migration/src/README.md` |
| Vault (agent session) | `AGENTS.md` |

When implementing **product** UI/API: surgical diffs, public-contract tests, no secrets.
When changing **harness**: do not put ORCH items in product `BACKEND_ROADMAP` Shaping.
