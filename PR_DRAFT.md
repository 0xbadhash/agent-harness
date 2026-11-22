# PR draft — root IoC scan requires each real home

**Spec:** .agents/specs/2026-11-08-security-root-ioc.md
**Plan:** .agents/specs/2026-11-08-security-root-ioc-plan.md

## What Problem This Solves

The weekly unit runs as root, so `Path.home()` is `/root`. The 2026-11-08 ship required the parent `/home` and could still report `status=ok` when a child home was never listed. `os.walk` swallows that error. A temp tree with a readable parent, a mode `000` child, and `keyv@6.0.0` inside the child returned `ok` and `pin_count=0`. The last vault JSON (2026-11-20) lists `scanned_roots` as `/home`, not the real homes under it.

## Why This Change Was Made

Each immediate child directory of `/home` is now a required root. `/root` is still walked and is not enough. The parent is not a scan root, so a parent walk cannot stand in for a child. If no child can be named, the result is `incomplete`. `--home` still replaces discovery. No username is hardcoded.

## User Impact

The Sunday timer's green line means each home directory under `/home` was entered. A home that could not be listed is `incomplete` (exit 2), not a green artifact. Operators who need a different tree pass `--home`.

## Evidence

The first pytest run failed with `TypeError` on `multiuser_home` (5 failed, 8 passed). That command passes now, so the executable red proof is the old contract: requiring exactly `/home` must not succeed.

```text
red_cmd: .venv/bin/python -c "import importlib.util; from pathlib import Path; p=Path('scripts/security_root_ioc_scan.py'); spec=importlib.util.spec_from_file_location('ioc', p); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); _roots, required = mod.resolve_home_roots(Path('/root'), []); raise SystemExit(0 if required == [Path('/home')] else 1)"
green_cmd: .venv/bin/python -m pytest -q tests/test_security_root_ioc_scan.py
```

Green result: 13 passed. CLI: `HOME=/root` `--print-roots --no-artifact` lists `required /home/debian`, `/home/denny`, and `/home/secondbrain`, and does not print a line `required /home`. `--home` to a missing or mode `000` directory exits 2. `--home` to a tree with `keyv@6.0.0` exits 1. `--home` to an empty readable directory exits 0.

## Evidence pack

| Item | Result |
|------|--------|
| pytest | 13 passed in `tests/test_security_root_ioc_scan.py` after the fix; 5 failed before it. `validate.py full` test_runner exit 0 |
| hard_gates | run at `/pr_review --validate` on this commit |
| smoke | `product_smoke.py` 2/2 passed (hardcodes, unit) |
| validate | `python3 scripts/validate.py full` 6/6 gates passed |

## Spec

**Spec:** `.agents/specs/2026-11-08-security-root-ioc.md`

## Traceability

| AC | Test / smoke |
|----|----------------|
| AC-1 | `test_root_process_home_requires_each_child_home` |
| AC-2 | `test_explicit_home_replaces_process_home` |
| AC-3 | `test_non_root_process_home_is_unchanged`, `test_deep_and_extra_root_still_append` |
| AC-4 | `test_missing_required_home_is_not_clean`, `test_unreadable_required_home_is_not_clean` |
| AC-5 | `test_pin_under_required_home_fails`, `test_payload_filename_under_required_home_fails` |
| AC-6 | `test_print_roots_for_root_process_home` |
| AC-7 | `test_unlistable_child_with_pin_is_not_clean` |
| AC-8 | `test_empty_multiuser_root_is_not_a_scanned_home` |

## Threat notes

- supply-chain: the scan exists to catch known malicious npm seed pins. A parent-only walk let a pin in an unlistable home look clean. Each child home is required, so a missed home is incomplete, not ok.
- path-traversal: `--home` is an operator-supplied path and replaces discovery. It is not joined onto a fixed root and it is not taken from file content. Tests use temp directories only.
- secrets: the status artifact records pin names and payload paths, not file bodies. No token is read into the markdown.

## Red-proof

```text
red_cmd: .venv/bin/python -c "import importlib.util; from pathlib import Path; p=Path('scripts/security_root_ioc_scan.py'); spec=importlib.util.spec_from_file_location('ioc', p); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); _roots, required = mod.resolve_home_roots(Path('/root'), []); raise SystemExit(0 if required == [Path('/home')] else 1)"
green_cmd: .venv/bin/python -m pytest -q tests/test_security_root_ioc_scan.py
```

## Cross-review

**Marker:** CROSS-REVIEW
**Range:** `HEAD~1...HEAD` for `6e616ba`, plus this draft fix.
**Secrets:** `check_secrets_diff.py --base HEAD~1 --head HEAD` clean.
**Blockers:** 0

### Security Guru

None. `status=ok` now requires each child of `/home` to be entered. An unlistable child is `incomplete` (exit 2), not a green scan. `--home` replaces discovery instead of appending a path the operator did not mean to treat as optional. No new credential surface.

### Maintainability Expert

None. Home selection stays in `resolve_home_roots` / `discover_real_homes`. Tests pass `multiuser_home` so the suite does not walk the live `/home`.

### Obsolete / cleanup (scoped)

No Tier A, B, or C delete. Confidence 0.9 that nothing in this diff is safe to remove. Evidence: `rg resolve_home_roots` hits the scanner and `tests/test_security_root_ioc_scan.py` only. The parent path `/home` remains the fallback required root when no child directory can be named. The systemd unit and `docs/ship-flow.md` still name this scan. Keep both.

### Domain Specialist

None. Domain hint is a portable harness with no host-only default. The script does not hardcode a username. On this host `--print-roots` with `HOME=/root` names `/home/debian`, `/home/denny`, and `/home/secondbrain`.

### Follow-ups

- Nested `os.walk` errors inside a home that was entered are still ignored. That is not the home-level false clean this item closes.
- `status=fail` still refreshes the ops dashboard even with `--no-artifact`. Pre-existing. Not changed.

## Things that look bad but are actually fine

1. **`/root` is still scanned.** Root-owned files stay in the walk. A clean `/root` cannot satisfy the required list.
2. **Other users' homes are required.** The parent used to be one walk of every child. Naming each child does not add a new tree. It stops a skipped child from looking clean.
3. **No username in the script.** Children of `/home` are discovered at run time. `--home` is the override when the real tree lives elsewhere.
4. **Exit 2 is not in `SuccessExitStatus`.** The timer should show the miss. That was already the rule.

## Test plan

- `tests/test_security_root_ioc_scan.py` (red, then 13 passed)
- `HOME=/root python3 scripts/security_root_ioc_scan.py --print-roots --no-artifact`
- `scripts/check_hardcodes.py`
