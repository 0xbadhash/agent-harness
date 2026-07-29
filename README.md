# agent-harness

<!-- CURRENT_RELEASE -->
**Current release:** `v1.4.5` (docs synced via `/sync_docs`)
<!-- /CURRENT_RELEASE -->


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

# 3. Install the harness into that product (+ verify ship skills)
"$AGENTS_HARNESS_ROOT/install_into_product.sh" . --verify

# 4. Bootstrap product identity + stack (edit the generated file)
$EDITOR .agents/product_plugin.yaml

# 5. Optional health check later
bash scripts/bootstrap_check.sh
python3 scripts/verify_skills.py
```

Then open the product in **any** coding LLM and run the ship skills  
(`/spec` → `/execute_dev` → `/code_review` → … → `/pr_review --validate` → `/release_mgmt` → `/sync_docs`).  
Always honor the printed **`NEXT_SKILL=`** line from `scripts/next_skill.py`.

**Any LLM bootstrap:** [docs/llm-bootstrap.md](docs/llm-bootstrap.md) — what to read, one-shot full-FSM phrase, phase gates, `NEXT_SKILL=` router.  
**Full FSM map:** [docs/ship-flow.md](docs/ship-flow.md).

**Pinned bootstrap:** use a release tag so every product gets a known-good harness:

```bash
git clone --branch v1.4.2 --depth 1 https://github.com/0xbadhash/agent-harness.git
```

---

## What you get

| Piece | Role |
|-------|------|
| **Skills** (`skills/*/SKILL.md`) | On-demand workflows: spec, TDD implement, code/cross/behavior review, PR score, release, sync docs, night readiness, handoff/session tools |
| **Scripts** (`scripts/`) | Deterministic gates: **pipeline FSM** ([ship-flow.md](docs/ship-flow.md)), validate, PR score, `next_skill`, hardcodes, vault writers, daytime readiness |
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
│  /spec  /execute_dev  /code_review  /cross_review       │
│  /behavior_validator  /pr_review  /release_mgmt         │
│  /sync_docs  /night_shift  /handoff  /sweep             │
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

Canonical detail: **[docs/ship-flow.md](docs/ship-flow.md)** (phases + skill branches + `NEXT_SKILL=`).

```text
init
  → /spec                      # optional; phase unchanged
  → /execute_dev               # TDD; set ready_for_review after reviews
       ├─ prose-only ──────────► /pr_review --validate
       └─ non-prose ──► /code_review
              ├─ large ──► /cross_review
              └─ runtime ► /behavior_validator
                    └──► /pr_review --validate   # only skill → approved|blocked
  → (if required) /vps_infra_ops --verify   # product-owned; phase stays approved
  → /release_mgmt              # smoke + tag → shipped
  → /sync_docs                 # → init
  → /qa_campaign               # optional deep QA after full FSM / huge release
```

Router (do not invent the next skill):

```bash
python3 scripts/next_skill.py --after execute_dev --base HEAD~1 --head HEAD
# → NEXT_SKILL=/code_review   (typical)

python3 scripts/next_skill.py --after sync_docs
# → NEXT_SKILL=/qa_campaign   (post full FSM; --skip-qa to finish)
```

Blocked path: `ready_for_review` → `blocked` → `/execute_dev` (remediation) → reviews → `/pr_review` again.

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
| [docs/night-shift.md](docs/night-shift.md) | Overnight readiness, gates, systemd 03:15 HKT, hard-stops |
| [docs/tdd.md](docs/tdd.md) | How `/execute_dev` enforces red→green |
| [docs/writing-skills.md](docs/writing-skills.md) | How to add a skill (Pocock-style minimal) |
| [docs/security.md](docs/security.md) | Third-party skills & secrets |
| [CHANGELOG.md](CHANGELOG.md) | Versions |

---

## Skills catalog (one line each)

Full table: **[docs/skills-catalog.md](docs/skills-catalog.md)**.

| Skill | Job |
|-------|-----|
| `/spec` | Constitution + interview + clarify → spec (+ optional plan/tickets) + roadmap OPEN |
| `/execute_dev` | One task, **TDD mandatory**; non-prose requires `/code_review` closeout; `NEXT_SKILL=` |
| `/code_review` | P0-first closeout after implement (required unless prose-only) |
| `/cross_review` | Multi-persona + obsolete scan when `NEXT_SKILL` says so |
| `/behavior_validator` | Source-blind behavior contract when runtime surface |
| `/pr_review` | Deterministic score (≥95) → `approved` / `blocked` |
| `/release_mgmt` | Smoke (plugin), version, tag → `shipped` |
| `/sync_docs` | Docs + optional vault release entry → `init` |
| `/qa_campaign` | Post-FSM deep E2E QA + bug hunt + root-cause fixes (suggested after `/sync_docs`) |
| `/night_shift` | Overnight readiness; vault TODO; **no** auto-ship — [night-shift.md](docs/night-shift.md) |
| `/handoff` | Clipboard handoff for a fresh agent |
| `/session_viewer` / `/agent_transcript` | Session HTML / sanitized transcript (ops) |
| `/sweep` | Hygiene pass |
| `/feedback` | Session notes (harness only) |
| `/audit_repo` / `/audit_harness` | Policy / harness gap scan |
| `/plan_backend` | Roadmap from gaps |
| `/test_automation` | Suite orchestration |

Product-only skills (`/vps_infra_ops`, deploy, host topology) live **in the product repo**, not here.

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

See the **Current release** stamp at the top of this README (and [CHANGELOG.md](CHANGELOG.md)).  
Pin installs with `git clone --branch vX.Y.Z`.
