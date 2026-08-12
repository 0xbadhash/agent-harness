# Scanner policy (Tier A-4)

**SoT:** `harness.manifest.yaml` → `scanner_policy`  
**Env override:** `SCANNER_STRICT=1` (or `true` / `yes` / `on`)

## Rules

| Check | Findings present | Tool missing (default) | Tool missing + `SCANNER_STRICT` |
|-------|------------------|------------------------|----------------------------------|
| Secrets (`check_secrets_diff.py`) | **Fail closed** | Regex fallback; fail only on findings | **Fail** if neither gitleaks nor trufflehog |
| Lockfile audit (`check_lockfile_audit.py`) | **Fail closed** | Warn + skip | **Fail** if no npm/pip-audit when lockfiles changed |
| Hardcodes (`check_hardcodes.py`) | Fail | n/a | n/a |

## Usage

```bash
# Local soft sandboxes (default)
python3 scripts/check_secrets_diff.py --base HEAD~1 --head HEAD

# CI / night shift fail-closed scanners
export SCANNER_STRICT=1
python3 scripts/check_secrets_diff.py --base HEAD~1 --head HEAD
python3 scripts/check_lockfile_audit.py --base HEAD~1 --head HEAD
```

CLI aliases: `--strict` / `--require-scanner` on secrets check also force scanner presence.
