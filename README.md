# agent-harness

**Reusable agent workflows for shipping software.**  
Not a framework. Not an app stack. A small set of **skills**, **scripts**, and **policy** you install into *any* product repo so the agent follows the same process every time.

> A prompt is a one-time instruction.  
> A **skill** is a reusable workflow file the agent loads when the task matches.  
> This repo is a **harness**: the skills + ship pipeline that sit beside your product—never inside another product’s domain code.

**Tech stack is not prescribed.** Python, TypeScript, Go, Rust, PHP—whatever you choose is declared at **bootstrap** in the product plugin. The harness only cares about: tests exist, gates pass, releases are intentional.

---

## Quickstart (2 minutes)

```bash
# 1. Clone the harness (once per machine)
git clone https://github.com/0xbadhash/agent-harness.git
export AGENTS_HARNESS_ROOT="$PWD/agent-harness"   # or install path

# 2. Create or open a product repo
mkdir my-product && cd my-product && git init

# 3. Install the harness into that product
"$AGENTS_HARNESS_ROOT/install_into_product.sh" .

# 4. Bootstrap product identity + stack (edit the generated file)
$EDITOR .agents/product_plugin.yaml
```

Then open the product in your coding agent and run the ship skills (`/spec` → `/execute_dev` → `/pr_review` → …).

**Pinned bootstrap:** use a release tag so every product gets a known-good harness:

```bash
git clone --branch v1.0.0 --depth 1 https://github.com/0xbadhash/agent-harness.git
```

---

## What you get

| Piece | Role |
|-------|------|
| **Skills** (`skills/*/SKILL.md`) | On-demand workflows: spec, implement (TDD), review, release, sync docs, anti-slop UI design, sweep |
| **Scripts** (`scripts/`) | Deterministic gates: pipeline FSM, validate, PR score, vault notes |
| **Policy** (`policy/`) | Always-on engineering rules the skills inherit |
| **Product plugin** | *Your* stack, smoke commands, vault path—never hard-coded in the harness |

### What you do **not** get

- A web framework or UI kit  
- A forced language or package manager  
- Another product’s source tree  
- Secrets, hosts, or deploy topology (those stay product-local)


## Source of truth (skills & policies)

**This repository** is the SoT for shared agent **skills** and **policies**.  
Products install a copy via `install_into_product.sh`; re-run install to refresh.

Personal knowledge vaults (e.g. second-brain / Obsidian) are **optional** and **off by default**.  
See `docs/source-of-truth.md` and `docs/second-brain-optional.md`. Never commit host-only vault paths as harness defaults.


---

## Mental model (push vs pull)

```text
┌─────────────────────────────────────────────────────────┐
│  Always-on (push)                                       │
│  policy/  ·  product AGENTS.md  ·  product_plugin.yaml  │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│  On demand (pull) — skills                              │
│  /spec  /execute_dev  /cross_review  /pr_review         │
│  /release_mgmt  /sync_docs  /night_shift  /sweep        │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│  Product code (your repo only)                          │
│  src / app / services / …  chosen by you at bootstrap   │
└─────────────────────────────────────────────────────────┘
```

---

## Ship flow

```text
init
  → /spec                 # constitution + clarify → acceptance (+ optional plan) + roadmap OPEN
  → /execute_dev          # TDD: red → green → refactor
  → /cross_review         # multi-persona (soft gate on large diffs)
  → /pr_review --validate # score ≥ 95
  → [product infra skill] # optional, product-owned
  → /release_mgmt         # smoke from product_plugin + tag
  → /sync_docs            # docs + optional vault release entry
  → init
```

Blocked path: `ready_for_review` → `blocked` → fix → re-run review.

---

## Documentation (start here)

Docs are **progressive**: short skill bodies, deep material only when linked.

| Doc | When to read |
|-----|----------------|
| [docs/overview.md](docs/overview.md) | Architecture & boundaries |
| [docs/bootstrap.md](docs/bootstrap.md) | Clone → install → plugin → first task |
| [docs/product-plugin.md](docs/product-plugin.md) | Stack, smoke, vault (bootstrap choices) |
| [docs/ship-flow.md](docs/ship-flow.md) | FSM, phases, artifacts |
| [docs/skills-catalog.md](docs/skills-catalog.md) | Each skill: purpose, when to fire |
| [docs/tdd.md](docs/tdd.md) | How `/execute_dev` enforces red→green |
| [docs/writing-skills.md](docs/writing-skills.md) | How to add a skill (Pocock-style minimal) |
| [docs/security.md](docs/security.md) | Third-party skills & secrets |
| [CHANGELOG.md](CHANGELOG.md) | Versions |

---

## Skills catalog (one line each)

| Skill | Job |
|-------|-----|
| `/spec` | Constitution + interview + clarify → spec (+ optional plan/tickets) + roadmap OPEN |
| `/execute_dev` | One task, **TDD mandatory**, single sub-task |
| `/anti_slop_design` | UI/UX design law (pols.dev): confirm, build without AI slop, pre-ship audit |
| `/night_shift` | Overnight readiness: test matrix, smoke, security, optional live probes; vault TODO only — **no** auto-ship |
| `/cross_review` | Security · maintainability · domain personas |
| `/pr_review` | Deterministic compliance score (≥95) |
| `/release_mgmt` | Smoke (from plugin), version, tag |
| `/sync_docs` | Drift reset, optional vault **release** entry |
| `/sweep` | Hygiene pass |
| `/feedback` | Session notes (harness only) |
| `/audit_repo` | Policy gap scan |
| `/plan_backend` | Roadmap from gaps |
| `/test_automation` | Suite orchestration |

Product-only skills (deploy, host topology) live **in the product repo**, not here.

---

## Updating the harness

```bash
cd "$AGENTS_HARNESS_ROOT" && git pull   # or checkout a newer tag
cd /path/to/product
"$AGENTS_HARNESS_ROOT/install_into_product.sh" .
# commit refreshed scripts/skills in the product if you vendor them
```

---

## Design principles

1. **Skills over prompts** — encode process once; reuse forever.  
2. **Product never owns another product** — plugin + install only.  
3. **Stack at bootstrap** — harness stays language-agnostic.  
4. **Progressive disclosure** — name/description first; full skill when needed.  
5. **Small skills** — one job per `SKILL.md`; link out for depth.  
6. **Deterministic gates** — scripts score; agents don’t freestyle release.  
7. **TDD for code** — red before green in `/execute_dev`.

Inspired by the Agent Skills open format and the “workflow in markdown” approach popularized by engineering skill packs (e.g. composable, failure-mode-driven skills).

---

## License

MIT — see [LICENSE](LICENSE).

## Version

**v1.0.0** — first stable bootstrap. Use the tag for production installs.
