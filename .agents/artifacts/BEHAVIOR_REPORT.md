# BEHAVIOR-REPORT

**Marker:** BEHAVIOR-REPORT
**Contract:** .agents/artifacts/BEHAVIOR_CONTRACT.md
**Target:** installed `ops-dashboard.service` / `ops-dashboard.timer` and the ops-dashboard rows in the systemd inventory

Checked with `systemctl show`, `systemctl is-enabled`, `systemctl cat`, and a read of the inventory phrases. The writer was not run.

## Results

| Clause | Status | Evidence |
|--------|--------|----------|
| 1 SuccessExitStatus=0 2 | pass | `systemctl show ops-dashboard.service -p SuccessExitStatus` → `SuccessExitStatus=0 2` |
| 2 timer enabled | pass | `systemctl is-enabled ops-dashboard.timer` → `enabled` |
| 3 four calendars | pass | `TimersCalendar` has `01:00:00 UTC`, `12:00:00 UTC`, `19:45:00 UTC`, and `23:45:00 UTC` (systemd prints the weekday set as `Mon..Thu,Sun`) |
| 4 service text | pass | `systemctl cat ops-dashboard.service` contains `intentional RED` and `SuccessExitStatus=0 2` |
| 5 timer text | pass | `systemctl cat ops-dashboard.timer` description contains `four` and names 01:00, 12:00, 19:45, and 23:45 UTC |
| 6 registry row | pass | inventory contains `intentional RED` and `SuccessExitStatus=0 2` (4 times each) plus the four clock marks |

## Summary

- pass: 6 · fail: 0 · blocked: 0
- `systemd-analyze verify` on the service and timer exited 0 after daemon-reload
- NEXT_SKILL=/pr_review --validate

---

## BEHAVIOR-REPORT — vault completion writer, live staging run (2026-11-09)

Judged by running the command, not by reading the code.

| # | Clause | Verdict | Evidence |
|---|--------|---------|----------|
| B1 | one command records a completion | pass | `hermes-done --id DEMO-VAULT-1 --verdict PARTIAL --needs-ceo …` printed `=== DONE DEMO-VAULT-1 PARTIAL ===` and wrote one event |
| B2 | the tag is matchable by the existing watcher regex | pass | tag matches `=== DONE [A-Z0-9-]+ (PASS|FAIL|PARTIAL|DONE|BLOCKED|BLOCKED-needs-CEO) ===` |
| B3 | a drain turns it into a vault note | pass | `vault-writer: DEMO-VAULT-1 written`; note at `…/_staging/2026-11-09/DEMO-VAULT-1.md` |
| B4 | frontmatter carries the decision fields | pass | 12 fields incl. `verdict: "PARTIAL"`, `needs_ceo: "true"`, `content_sha256` |
| B5 | the body is inert | pass | attack fixture rendered as `&lt;script>`, no backticks, no `~~~` line |
| B6 | the spool empties and the event becomes read-only evidence | pass | spool empty after drain; `processed/DEMO-VAULT-1.json` mode 444 |

**6 pass · 0 fail.** Known limit: systemd activation itself (A7) was verified from the unit text, not by watching
a real trigger — the units are not installed while the vault rule is unstamped.

---

# BEHAVIOR-REPORT — root IoC real homes (2026-11-22)

**Marker:** BEHAVIOR-REPORT
**Contract:** clauses below, checked by CLI only (`--print-roots` and `--home`), not by reading the scanner source during scoring.
**Target:** `scripts/security_root_ioc_scan.py`

| # | Clause | Verdict | Evidence |
|---|--------|---------|----------|
| B1 | `HOME=/root` plan names each real home and does not claim a clean scan | pass | `--print-roots --no-artifact` exit 0. Lines include `required /home/debian`, `required /home/denny`, `required /home/secondbrain`. No line `required /home`. No `status=ok`. Vault dir passed as `PRODUCT_VAULT_ROOT` stayed empty. |
| B2 | a home that does not exist is not green | pass | `--home` to a missing path printed `status=incomplete` and exited 2. |
| B3 | an unlistable home that holds a known pin is not green | pass | `--home` to a mode `000` directory printed `status=incomplete`, `pins=0`, exit 2. |
| B4 | a readable home with `keyv@6.0.0` fails | pass | `--home` to that tree printed `status=fail`, `pins=1`, exit 1. |
| B5 | a readable empty home is a real clean | pass | `--home` to an empty directory printed `status=ok` and exited 0. |

**5 pass · 0 fail.** Limit: the plan check does not walk the live homes. The pin case also invoked `ops_dashboard --write` (refresh rc=1). `security-ioc-last.json` mtime stayed 2026-11-20.
