# Plan: Root IoC scan home selection

- **Spec:** `.agents/specs/2026-11-08-security-root-ioc.md`
- **Product:** agent-harness
- **Created:** 2026-11-08
- **Status:** ready-for-agent

## Stack & constraints

Python 3, stdlib only, pytest. No new service. No username hardcoded. Do not edit the dirty `ops_dashboard.py` tree. Do not tag or push.

## Approach

Split home selection out of `main`. `resolve_home_roots` returns the homes to walk and the homes that must have been entered. `assemble_roots` adds `/opt`, containerd when `--deep`, and each `--root`. `run_scan` sets `status=incomplete` when a required home is missing from `scanned_roots`. `exit_code` maps fail to 1, ok to 0, and anything else to 2. The markdown artifact is green only for `ok`. `--print-roots` prints the plan and returns before any walk or vault write.

When the process home is `/root` and `--home` is omitted, the required home is `/home` and `/root` is still walked. `--home` replaces both.

## Architecture decisions

- Module: `scripts/security_root_ioc_scan.py` only. Callers of `run_scan` gain an optional `required` list. Default `None` keeps the old ok/fail behavior for a fully walked list.
- `scan_tree` returns whether `os.walk` entered the tree. A `PermissionError` means that root was not scanned. Pins already collected are kept, so a partial walk that saw a payload still fails.
- Dashboard code is unchanged. Any JSON status other than `ok` or `fail` is already attention.
- The systemd unit comment records the rule. `SuccessExitStatus` stays `0 1`.

## File / surface map (indicative)

| Area | Change |
|------|--------|
| `scripts/security_root_ioc_scan.py` | Home resolver, incomplete status, `--home`, `--print-roots` |
| `tests/test_security_root_ioc_scan.py` | Temp-tree tests. No live `/home` or `/opt` walk |
| `deploy/security-root-ioc.service` | Comment only |
| `docs/ship-flow.md` | One sentence on the required home |

## Implementation sequence

1. Failing tests for `/root`, `--home`, incomplete, pins, and `--print-roots`.
2. Implement the resolver, status, and CLI in the scanner.
3. Prove green on the temp trees, then the plugin smoke and `validate.py full`.

## Testing plan

- Seams: `resolve_home_roots`, `assemble_roots`, `run_scan`, `exit_code`, `write_artifacts`, `main(..., process_home=)`.
- Smoke: `scripts/check_hardcodes.py` and `scripts/smoke_unit.sh`.
- Manual: `HOME=/root python3 scripts/security_root_ioc_scan.py --print-roots --no-artifact`.

## Risks & mitigations

| Risk | Mitigation |
|------|------------|
| A clean `/root` still reports ok | `/home` is required when the process home is `/root` |
| `--print-roots` looks like a clean scan | It does not print `status=ok` and it does not write artifacts |
| Walking all of `/home` is slow | That is the documented surface. Tests stay on temp dirs |

## Open questions

None. The operator instruction and the script header settle `/home` plus `--home`.
