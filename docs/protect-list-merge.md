# Protect-list merge playbook (HSQ-2)

Harness `install_into_product.sh` **never overwrites** scripts listed in
`config/default_protect_scripts.txt` (or product `.agents/harness_protect_scripts.txt`).

## Report drift

```bash
cd ~/agent-harness
python3 scripts/portfolio_install_report.py --protect-drift
# see .agents/artifacts/PORTFOLIO_INSTALL_REPORT.md
```

## Top recurring forks on this VPS

| Script | Typical reason to fork | Merge strategy |
|--------|------------------------|----------------|
| `scripts/check_hardcodes.py` | product allowlists (RSS, newsjack) | Port allowlist deltas into SoT carefully; re-install non-forked products |
| `scripts/night_shift_readiness.py` | product gate lists / timeouts | Prefer plugin config over fork; if must fork, rebase onto SoT monthly |
| `scripts/kanban_ensure_spec.py` | second-brain kanban_schema path | Keep product-local; document in product AGENTS.md |
| `scripts/pipeline_state.py` | rarely should fork | Prefer SoT after HSQ-2 transitions |
| `scripts/pr_validator.py` | product score weights | Avoid; use SoT |

## Manual merge recipe

```bash
# 1) Diff protect file vs SoT
diff -u ~/PRODUCT/scripts/check_hardcodes.py ~/agent-harness/scripts/check_hardcodes.py | less

# 2) Port product-only allowlist lines into a product-local allowlist file if possible
# 3) Or copy SoT then re-apply product patches
cp ~/agent-harness/scripts/check_hardcodes.py ~/PRODUCT/scripts/
# re-apply product allowlist commits

# 4) Remove from protect list only when product no longer needs a fork
#    edit .agents/harness_protect_scripts.txt

# 5) Force portable reinstall (still skips protect list)
cd ~/agent-harness && python3 scripts/portfolio_install_report.py --install --force
```

## Policy

- **Do not** silently drop protect entries in automation.
- **Do** review protect drift weekly via OPS-DASHBOARD / portfolio report.
