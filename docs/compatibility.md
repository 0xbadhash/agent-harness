# Compatibility matrix (claimed vs tested)

**SoT:** `harness.manifest.yaml` → `compatibility`  
**Check:** `python3 scripts/check_compatibility.py`

Legend: **claimed** = design intent · **tested** = exercised on this portfolio VPS · **unsupported** = not a goal

## Coding agents (hosts)

| Host | Claimed | Tested | Notes |
|------|:-------:|:------:|-------|
| Grok Build / Grok CLI | yes | **yes** | Primary host on catalyxt VPS |
| Cursor | yes | partial | Skills via AGENTS.md; not CI-gated |
| Claude Code | yes | untested | Same skill markdown contract |
| Generic LLM CLI (`-p`) | yes | partial | Ship scripts are plain Python |

## Skills / workflow

| Capability | Claimed | Tested |
|------------|:-------:|:------:|
| Skill discovery (SKILL.md) | yes | yes |
| `next_skill.py` routing | yes | yes |
| Deterministic gates (`hard_gates`, `pr_validator`) | yes | yes |
| Pipeline FSM (`pipeline.json` + legal transitions) | yes | yes |
| Artifact generation (CODE-REVIEW, etc.) | yes | yes |
| Handoff / remaining / session context | yes | yes |
| Release approval (score ≥95, human tag) | yes | yes |
| Auto-resume after host crash | no | n/a — recovery: resumable only |

## Languages / stacks (product_plugin)

| Stack | Claimed | Tested on portfolio |
|-------|:-------:|---------------------|
| Python | yes | **yes** (most products + harness) |
| TypeScript / JS | yes | **yes** (catalyxt, bip39 web, zk app, substack) |
| PHP | yes | partial (watchlist migration) |
| Go / Rust | yes | untested lifecycle |

## Platforms

| Platform | Claimed | Tested |
|----------|:-------:|:------:|
| Linux VPS | yes | **yes** |
| macOS / Windows dev | yes | untested locking / paths |

## Update policy

When you test a new host/language, update both this table and `harness.manifest.yaml` `compatibility.tested`.
