# MCP integration (Tier B-1)

agent-harness does **not** own an MCP server runtime. Products attach MCP tools via host configuration (Grok Build, Claude, Cursor).

## Contract

| Item | Status |
|------|--------|
| Own MCP process | NON_GOAL |
| Document common MCP attachments | yes (this page) |
| Validate optional `mcp` block in product_plugin | `scripts/check_mcp_contract.py` (warn) |

## Common portfolio attachments

| Server | Used by | Purpose |
|--------|---------|---------|
| `mcp-obsidian` | second-brain, email-detach | Vault read/write |
| `github` | most products | Issues/PRs/Actions |
| `tasks` | portfolio ops | Lightweight task lists |
| product-specific | catalyxt, buzz, … | Domain tools |

## product_plugin optional keys

```yaml
mcp:
  required: []          # names that must be configured in host (warn only)
  documented: [github, mcp-obsidian]
```

Run: `python3 scripts/check_mcp_contract.py --root .`
