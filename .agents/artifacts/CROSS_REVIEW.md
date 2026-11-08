# CROSS-REVIEW

**Marker:** CROSS-REVIEW
**Base:** 56a4b3c6ea620d8c637b165579f70a27825fbb85
**Head:** 6ea5fb1
**Blockers:** 0
**Majors:** 0

## Security

None. The weekly unit is already `User=root`. This diff stops `status=ok` when that process home is `/root` and `/home` was not walked. `--home` and `--root` are local operator paths passed to `Path` and `os.walk` (`followlinks=False`), not a shell. Finding lines stay paths, not file bodies. No new credential, no new listener.

## Maintainability

None. Home selection is `resolve_home_roots` / `assemble_roots`, covered by `tests/test_security_root_ioc_scan.py`. `scan_tree` now returns whether the walk entered the tree. The only caller is `run_scan` in the same file (`rg scan_tree` hits that file only).

### Obsolete / cleanup (scoped)

Touched paths: `scripts/security_root_ioc_scan.py`, `tests/test_security_root_ioc_scan.py`, `deploy/security-root-ioc.service`, `docs/ship-flow.md`, spec, changelog, PR draft.

| Tier | Item | Conf | Verdict | Evidence |
|------|------|------|---------|----------|
| C | `Path.home()` default in `main` | 0.1 | keep | Still the process home for non-root runs. `--home` replaces it. `rg` shows the call at `security_root_ioc_scan.py` main. |
| C | `--root` | 0.1 | keep | Still appended after the home. Test `test_deep_and_extra_root_still_append` asserts `/var/extra-ioc`. |
| C | Walk of `/root` when process home is `/root` | 0.2 | keep | Not sufficient for `status=ok`. `/home` is the required root. Dropping `/root` would hide root-owned IoCs. |
| A | none | | | No doc-only rot or unreferenced helper in this diff. |

No Tier A deletions. Whole-repo cruft was not scanned.

## Domain

None. Plugin hints are a portable harness and no secret leakage. The scanner already names `/opt` and containerd. The header already named `/home`. This change matches that header and does not hardcode a username. `status=ok` now means the required home was entered.

## §9

1. Exit 2 is outside `SuccessExitStatus` so a missed home fails the timer. Findings stay exit 1.
2. `/root` is still walked. It does not make the scan green by itself.
3. `--print-roots` exits 0 and must not print `status=ok`, because nothing was walked.
