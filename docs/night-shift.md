# Night shift readiness (`/night_shift`)

**ORCH-P3** overnight / on-demand **readiness** for product test surfaces.  
**Source of truth:** this repo (`agent-harness`). Products get the skill + scripts via `install_into_product.sh`.

| | |
|--|--|
| Skill | `skills/night_shift/SKILL.md` |
| Single product | `scripts/night_shift_readiness.py` |
| Multi-product | `bin/night_shift_all_products.py` |
| Product registry | `config/night_shift_products.yaml` |
| systemd | `deploy/night-shift-all.service` + `deploy/night-shift-all.timer` |
| Test matrix helper | `scripts/check_test_matrix.py` |
| Coverage (ORCH-P3b) | `scripts/check_module_coverage.py` + `config/coverage_config.example.json` |

---

## What it is / is not

| **Is** | **Is not** |
|--------|------------|
| Proves suites / gates are green so the next `/execute_dev` can start | A product UI feature |
| Report-only: artifacts + optional vault TODO/log | Autonomous overnight coding |
| Multi-product orchestrator on a schedule | Auto `/release_mgmt`, tag, or force-push |
| Optional live HTTP probes from plugin config | Permission to “fix” product code without a human |

### Human hard-stops (always)

1. **Never** run `/release_mgmt`, create tags, or force-push from night_shift.  
2. **Never** auto-edit product code to “fix” failures — **report only**.  
3. **Never** invent roadmap features.  
4. Failures → checkboxes in vault **TODO** (and repo `.agents/artifacts/`).

---

## Architecture

```text
                    ┌─────────────────────────────────────┐
                    │  night-shift-all.timer (systemd)    │
                    │  19:15 UTC = 03:15 HKT daily         │
                    └─────────────────┬───────────────────┘
                                      │
                                      ▼
                    bin/night_shift_all_products.py
                    (reads config/night_shift_products.yaml)
                                      │
              ┌───────────────────────┼───────────────────────┐
              ▼                       ▼                       ▼
     product A/scripts/     product B/...          harness --root
     night_shift_readiness  night_shift_readiness  night_shift_readiness
              │                       │                       │
              ▼                       ▼                       ▼
     gates (matrix, smoke, …)   same                    same
              │                       │                       │
              ├─ .agents/artifacts/NIGHT_SHIFT_*.md
              └─ vault 01-Projects/<label>/{night-shift-log,TODO}.md
                                      │
                                      ▼
                    vault 01-Projects/harness-night-shift/
                      SUMMARY.md · TODO.md · log.md
```

---

## Single product (manual or agent)

From a **product** checkout (after install):

```bash
cd /path/to/product
export PRODUCT_VAULT_ROOT=/path/to/vault   # optional; skip if unset / missing

python3 scripts/night_shift_readiness.py
python3 scripts/night_shift_readiness.py --quick          # fast gates only
python3 scripts/night_shift_readiness.py --skip-live      # no HTTP probes
python3 scripts/night_shift_readiness.py --dry-run        # print report, no writes
python3 scripts/night_shift_readiness.py --json           # machine-readable summary
```

From **harness SoT** against any product root:

```bash
cd /path/to/agent-harness
python3 scripts/night_shift_readiness.py \
  --root /path/to/product \
  --vault "${PRODUCT_VAULT_ROOT:-/opt/second-brain/vault}"
```

### Gates (when the matching script exists)

| Gate | Script / mechanism | Notes |
|------|--------------------|--------|
| test_matrix | `check_test_matrix.py` + `.agents/policy/TEST_MATRIX.md` | Paths **exist**, not pass/fail of tests |
| repo_hygiene | `check_repo_hygiene.py` | If present |
| hardcodes | `check_hardcodes.py` | If present |
| verify_skills | `verify_skills.py` | If present |
| validate_full | `validate.py full` | Full mode only (`--quick` skips) |
| product_smoke | `product_smoke.py` | From `product_plugin.smoke` |
| coverage | `check_module_coverage.py --run --soft-if-missing` | Soft skip if no pytest-cov |
| security_* | optional pytest / PHPUnit security files | If present |
| live_http / static_denies | curl / product deny script | If not `--skip-live` |

Missing tools are **skipped** so the runner stays portable across products.

### Artifacts (per product)

| Path | Content |
|------|---------|
| `.agents/artifacts/NIGHT_SHIFT_REPORT.md` | Full markdown report |
| `.agents/artifacts/NIGHT_SHIFT_TODO.md` | Recommendations + gate checkboxes |
| `01-Projects/<project_label>/night-shift-log.md` | Append-only (vault, if available) |
| `01-Projects/<project_label>/TODO.md` | Overwritten auto section + human backlog |

Exit code: **0** = all gates pass; **1** = one or more failures (reports still written).

---

## Multi-product orchestrator

```bash
cd /path/to/agent-harness
python3 bin/night_shift_all_products.py \
  --vault "${PRODUCT_VAULT_ROOT:-/opt/second-brain/vault}"
```

### Product registry

Default file: `config/night_shift_products.yaml`

```yaml
# product_id: path  (~ expanded)
watchlist: ~/watchlist
email-detach: ~/email-detach
# ...
```

Override: env `NIGHT_SHIFT_PRODUCTS_FILE=/path/to/other.yaml`.

For each existing directory, the orchestrator prefers  
`<product>/scripts/night_shift_readiness.py`, else harness SoT with `--root`.

### Multi-product vault outputs

| Path | Content |
|------|---------|
| `01-Projects/harness-night-shift/SUMMARY.md` | Latest all-product table |
| `01-Projects/harness-night-shift/TODO.md` | Cross-product checkboxes |
| `01-Projects/harness-night-shift/log.md` | Append-only multi reports |
| `.agents/artifacts/NIGHT_SHIFT_ALL_REPORT.md` | Repo-side multi summary (harness) |

---

## product_plugin knobs

Optional block in the **product** `.agents/product_plugin.yaml`:

```yaml
night_shift:
  default_host: ""           # e.g. app.example.com (no scheme); prefer PRODUCT_BASE_URL env
  live_path: ""              # path under https://default_host when no live_urls
  live_urls: []              # full URLs for HTTP probes
  live_expect_code: "200"
  coverage_soft: "1"         # "0" = hard-fail if coverage tooling missing
```

Vault label for TODO/log:

```yaml
vault:
  enabled: true              # optional overall vault
  root_env: PRODUCT_VAULT_ROOT
  project_label: my-product  # → 01-Projects/my-product/
```

Also used: `PRODUCT_BASE_URL` or `WATCHLIST_BASE_URL` for live probes.

---

## Test matrix

Optional product file: `.agents/policy/TEST_MATRIX.md`  
Example shape: `policy/TEST_MATRIX.example.md` in this repo.

```markdown
| id | surface | must_exist |
|----|---------|------------|
| unit | core unit tests | tests/test_foo.py, tests/test_bar.py |
```

`check_test_matrix.py` fails if any listed path is missing.

---

## Coverage (ORCH-P3b)

1. Copy `config/coverage_config.example.json` → product `config/coverage_config.json` (or harness).  
2. Night shift runs `check_module_coverage.py --run --soft-if-missing` when the script is installed.  
3. Daytime: `./tools/bin/lint_and_test.sh --coverage` after `install_into_product.sh`.

---

## systemd schedule (VPS)

| Field | Value |
|-------|--------|
| Wall clock intent | **03:15 Asia/Hong_Kong (HKT)** |
| Host timer | **19:15 UTC** daily (`OnCalendar=*-*-* 19:15:00 UTC`) |
| Random delay | up to **120s** |
| Units | `night-shift-all.timer` → `night-shift-all.service` |
| User | `debian` (see service file) |
| WorkingDirectory | harness checkout path in the unit file |

### Install / enable (once)

```bash
HARNESS="$HOME/agent-harness"   # or wherever the harness checkout lives
sudo cp "$HARNESS/deploy/night-shift-all.service" \
        "$HARNESS/deploy/night-shift-all.timer" \
        /etc/systemd/system/
# Units use systemd %h (user home) — no hardcoded /home/<user> paths.
sudo systemctl daemon-reload
sudo systemctl enable --now night-shift-all.timer
```

Disable legacy single-product timer if present:

```bash
sudo systemctl disable --now night-shift-readiness.timer 2>/dev/null || true
```

### Ops checks

```bash
systemctl is-enabled night-shift-all.timer
systemctl status night-shift-all.timer --no-pager
systemctl list-timers | grep night-shift-all
journalctl -u night-shift-all.service -n 80 --no-pager

# Manual one-shot (same as timer would run):
sudo systemctl start night-shift-all.service
```

Service treats exit **0 and 1** as success for systemd (`SuccessExitStatus=0 1`) so a failed product gate still counts as a completed overnight run; check the report for PASS/FAIL.

### Live status on this host (documented when last verified)

| Field | Value (2026-07-17) |
|-------|---------------------|
| Enabled | yes |
| Active | active (waiting) |
| Last trigger | 2026-07-16 19:15:41 UTC |
| Schedule | daily ~19:15–19:17 UTC |

Re-verify with the ops checks above after unit edits or reboot.

---

## Install into products

```bash
export AGENTS_HARNESS_ROOT=/path/to/agent-harness
"$AGENTS_HARNESS_ROOT/install_into_product.sh" /path/to/product
```

That rsyncs portable skills (including `night_shift`) and scripts (including `night_shift_readiness.py`, `check_test_matrix.py`, coverage helper) and optionally `tools/`.

**Not** installed into products: `bin/night_shift_all_products.py`, `deploy/*`, multi-product `config/night_shift_products.yaml` — those stay harness-host only.

---

## Agent skill `/night_shift`

When invoked in a product checkout, the agent should:

1. Run `python3 scripts/night_shift_readiness.py` with appropriate flags.  
2. Summarize PASS/FAIL and point at artifacts / vault TODO.  
3. **Not** start `/release_mgmt` or edit product code to silence failures without an explicit human task.

Full skill text: `skills/night_shift/SKILL.md`.

---

## Security notes

- Live probes and vault paths may be **host-specific**; keep secrets out of yaml.  
- Prefer env (`PRODUCT_BASE_URL`, `PRODUCT_VAULT_ROOT`) over committed hostnames.  
- Public harness defaults stay vault-agnostic; this VPS unit file may set `/opt/second-brain/vault` for **this** host only.

---

## Related

- [Skills catalog](skills-catalog.md)  
- [Product plugin](product-plugin.md)  
- [Ship flow](ship-flow.md) (night_shift is **off** the ship FSM — readiness, not a phase)  
- [Optional vault](second-brain-optional.md)  
- [Source of truth](source-of-truth.md)  
