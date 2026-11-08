# CROSS-REVIEW

**Marker:** CROSS-REVIEW
**Base:** HEAD~1
**Head:** HEAD (`18c2674`)
**Blockers:** 0
**Majors:** 0
**Tier A obsolete:** 0

## Security Guru

None. The diff deletes the hardcoded vault fallback in `scripts/challenge.py`. `check_secrets_diff.py --base HEAD~1 --head HEAD` printed `secret scan clean`. Schema lint still rejects an unregistered project and a `herm-config` subdirectory. No new network call, shell, or credential.

## Maintainability Expert

None. `project_rel` is the one label helper `challenge.py` calls. The new tests cover the missing-plugin path, the explicit plugin label, the portable `mission-feeds` row, and the schema allow/deny cases. The unused `subprocess` import in `kanban_fs.py` is gone.

### Obsolete / cleanup (scoped)

| Item | Conf | Verdict | Evidence |
|------|-----:|---------|----------|
| Tier C — `sync_docs_full.py` `or "product"` and `sync_vault_devlog.py` `or "product"` | 0.2 | keep | Still the fallback when a plugin label is empty. Not referenced by the new tests. Not the writer that created `01-Projects/product/` via `challenge._vault_paths`. |
| Tier C — `night_shift_readiness._safe_label` returns `product` for an empty or unsafe segment | 0.2 | keep | Call site passes `project_label or product_id or ROOT.name` before `_safe_label`. Invalid segments still need a single-segment substitute. |
| Tier C — `vault_schema_lint` allow of `challenges/` and `INDEX.md` | 0.1 | keep | `challenge.py` writes `challenges/`. Live projects already have `INDEX.md`. Stranger folders still fail (`test_unregistered_project_and_unknown_root_still_fail`). |

Out of scope for a repo-wide cruft pass — run `/sweep`.

## Domain Specialist

None. Domain hints are portable harness, no host-only defaults, no secret leakage. The registry row is `mission-feeds: ~/.local/lib/mission-feeds`. The plugin label is `mission-feeds`. `herm-config` stays a files-only stub and is not added to `night_shift_products.yaml`.

## Things that look bad but are actually fine

1. Widening `ROOT_ALLOW` and `PROJECT_DIR_ALLOW` looks like silencing the gate. Unregistered names and unknown roots still fail the new tests.
2. Refusing the `/opt/second-brain/vault` fallback looks like it breaks challenge on this host. `PRODUCT_VAULT_ROOT` or `--vault` still selects the vault. Only the silent host default is gone.
3. The night "absolute host paths" proposal looks like open work. It matched allow-listed `/home/browser` lines in the hardcodes printout. `check_hardcodes` was already green.

## Follow-ups

- Empty-label `"product"` fallbacks in `sync_docs_full.py` and `sync_vault_devlog.py` remain. Not this diff.
