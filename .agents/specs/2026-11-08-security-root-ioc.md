# Root IoC scan must not go green from /root alone

- **Product:** agent-harness
- **Created:** 2026-11-08
- **Status:** ready-for-agent
- **Priority:** P1
- **Roadmap:** CHANGELOG.md → Open work
- **Plan:** `.agents/specs/2026-11-08-security-root-ioc-plan.md`
- **Tracker:** local
- **Constitution:** policy defaults (no `.agents/CONSTITUTION.md` or root `AGENTS.md`)
- **Grill-me:** complete

## Problem Statement

`deploy/security-root-ioc.service` runs `scripts/security_root_ioc_scan.py` as `User=root`. `Path.home()` is then `/root`. The weekly scan walks `/root` and `/opt` (and containerd when `--deep`) and can write `status=ok`. Product trees live under the real home (on this host, a child of `/home`). A green OPS-DASHBOARD line and a green `security-ioc-status.md` can be a false clean: the operator home was never opened.

The 2026-11-08 ship required the parent `/home` as one root. That is still a false clean. `os.walk` does not raise when a child directory is unlistable, and the scanner records the parent as scanned. A known pin inside that child is then `status=ok` with `pin_count=0`. Reproduced on a temp tree: parent readable, child mode `000`, `keyv@6.0.0` in the child's lockfile, `run_scan([parent], required=[parent])` returns `ok`.

## Solution

When the process home is `/root` and the operator does not pass `--home`, each immediate child directory of `/home` is a required home. `/root` is still walked and is not sufficient. The parent `/home` is not a required root and is not a substitute for those children. If no child directory can be named (parent missing, unlistable, or empty), the result is `status=incomplete`: the parent path is the missing required home, and a walk of the parent does not count. A missing or unreadable required home is `status=incomplete` (not `ok`, not a green artifact, exit 2). Passing `--home` (repeatable) replaces that discovery, and each of those paths is required. A normal user's `Path.home()` is unchanged. Do not hardcode a username.

## User Stories

1. As the operator, I want the Sunday root timer to scan each real home under `/home`, so a clean `/root` or a walk that only entered the parent cannot mark the host green.
2. As the operator, I want to pass `--home` when the real tree is not a child of `/home`, so the same script works without hardcoding a username.
3. As the operator, I want a scan that never opened a required home to show incomplete, so the dashboard does not draw a green line for a scan that did not look.

## Implementation Decisions

- Surface: `scripts/security_root_ioc_scan.py`, its unit tests, the systemd unit comment, and the one ship-flow sentence that describes this scan.
- `--home` replaces `Path.home()`. It does not append. Repeatable. Each value is required. Discovery of children does not run.
- No `--home` and process home resolves to `/root`: required homes are the immediate child directories of `/home` (sorted by name). `/root` is walked and is not required. Then `/opt`, then `/var/lib/containerd` if `--deep`, then each `--root`. The parent `/home` is not walked as a root (no double walk) and cannot satisfy the required list.
- No child directory can be named: required is `/home` itself, and that path is not treated as scanned. Result is `incomplete`.
- No `--home` and process home is anything else: scan that home only (required), plus the same system and `--root` paths as today.
- `status=ok` only when no pins, no payload names, and every required home was a readable directory that was walked. Otherwise `incomplete` if the gap is coverage, `fail` if a pin or payload was found.
- Exit 0 ok, exit 1 findings, exit 2 incomplete. Do not add 2 to `SuccessExitStatus` (the timer should show the miss).
- Artifact emoji is green only for `ok`.
- `--print-roots` prints the planned roots and exits without walking or writing artifacts. It must not print `status=ok`.
- Do not hardcode a username. `/home/debian` stays out of the script.

## Testing Decisions

- Public seams: `resolve_home_roots`, `discover_real_homes`, `assemble_roots`, `run_scan`, `exit_code`, `write_artifacts`, and `main(..., process_home=..., multiuser_home=...)` with `--print-roots`.
- Fixtures live under a temp directory. Tests pass `multiuser_home` and do not walk `/home`, `/opt`, or `/var/lib/containerd`.
- Commands: `python3 -m pytest -q tests/test_security_root_ioc_scan.py`, then plugin smoke (`scripts/check_hardcodes.py` and `scripts/smoke_unit.sh`) as far as this item can run them.

## Acceptance Criteria

- [x] AC-1 With process home `/root`, no `--home`, and a multi-user root that contains two child directories, both children are required, `/root` is walked and is not required, and the parent directory is not the required home.
- [x] AC-2 `--home PATH` (one or more) replaces the process home. Those paths are the required homes. Discovered children are not added beside them.
- [x] AC-3 A process home other than `/root` stays the only home root. `--deep` still adds containerd. `--root` still appends.
- [x] AC-4 If a required home is missing or not a readable directory, `status` is `incomplete`, the exit code is 2, and the markdown artifact is not green and does not say the scan found nothing malicious.
- [x] AC-5 A `keyv@6.0.0` lock pin or a known payload filename under a required home that was scanned yields `status=fail` and exit 1.
- [x] AC-6 `--print-roots` with process home `/root` lists each discovered child as required, exits 0 without writing a vault artifact, and does not print `status=ok`.
- [x] AC-7 A readable parent with an unlistable child that holds `keyv@6.0.0` is not `status=ok`. That child is missing-required and the exit code is 2.
- [x] AC-8 An empty multi-user root, with process home `/root` and no `--home`, is not `status=ok`.
- [x] Product smoke commands succeed, or the log names any failure that is outside this item.
- [x] No secrets committed.

## Out of Scope

- Editing `scripts/ops_dashboard.py` (working tree already has unrelated edits). Unknown JSON status already lands on the attention list.
- Hardcoding `/home/debian` in the unit or the script.
- Changing `SuccessExitStatus`, the timer calendar, or making a missing `/opt` or containerd path fail the scan.
- Walking the live host as the test suite.
- Tagging, pushing `main`, rotating credentials, or deleting vault or OneDrive files.
- A new malware signature list.

## Grill-me

**Status:** complete
**Date:** 2026-11-08

### G1 Outcome
- Q: What does done look like in one sentence the operator would say?
  - A: The root timer scans the real home (or the home I pass in), and a green result means that home was actually scanned.
  - Recommended was: the same. Operator instruction: "Path.home()=/root skips /home/debian, so a green result can be false-clean. Scan the real home or take it as an argument."

### G2 Non-goal / kill
- Q: What must this ship not do, and what would cancel it?
  - A: Do not hardcode a username, do not edit the unrelated ops-dashboard diff, do not tag or push, do not rotate credentials, and do not delete vault or OneDrive files. Cancel if the only way to name the home is a new product decision the timer unit and the script header do not already support.
  - Recommended was: no new scanner and no second scheduler. The header already names `/home`, and `--root` already exists but only as an extra path, so a replacing `--home` is the argument the instruction allows.

### G3 Wrong product
- Q: Is this the wrong surface (dashboard copy, a one-off sudoers change, or a debian-only unit path)?
  - A: The false clean is `security_root_ioc_scan.py` choosing `Path.home()` while `deploy/security-root-ioc.service` sets `User=root`. The fix belongs in that script. The unit only needs a comment so the next reader sees why `/root` is not sufficient.
  - Recommended was: the script the timer executes. Evidence: `User=root`, `ExecStart=...security_root_ioc_scan.py`, and `roots` starting at `Path.home()`.

### G4 Cheapest alternative
- Q: What is the smallest ship that still stops the false clean?
  - A: When the process home is `/root`, require `/home` (still walk `/root`). Add `--home` so an operator can replace that default. Do not add a new daemon.
  - Recommended was: that union. "Scan the real home" matches the script header (`/home`). "Or take it as an argument" is `--home`, because existing `--root` does not replace `Path.home()`.

### G5 Abuse / failure
- Q: How does this fail or get misused?
  - A: If `/home` is missing, status stays ok today and the dashboard goes green. That must become incomplete, exit 2, and a non-green artifact. `--home /root` is an explicit operator choice and may be ok. `--print-roots` must not be able to print `status=ok` without a walk.
  - Recommended was: fail closed on a required home that was not walked. Do not treat optional `/opt` or containerd gaps as this bug.

### G6 Verify
- Q: How do we prove it before merge?
  - A: Unit tests on temp trees plus `--print-roots` with `process_home=/root`. No live walk of `/home` or `/opt` in the suite. Plugin smoke after the tests.
  - Recommended was: product smoke plus the new unit module.

### G7 Priority / delay
- Q: Why now, and what happens if we ship nothing?
  - A: The weekly timer can keep reporting green without opening the product trees. This item is the assigned job. Priority P1 (the operator did not call it a hotfix). Shipping nothing leaves the false clean in place.
  - Recommended was: P1 unless the operator said P0 or hotfix.

## Clarifications

### 2026-11-08
- Q: When the process home is `/root`, do we drop `/root` or scan it beside `/home`?
  - A: Scan both. `/home` is required for `status=ok`. `/root` is still walked so root-owned IoCs are not ignored. `--home` replaces both. Recommended default from the header (cover `/home`) plus no loss of the path the code already walks.
- Q: If the required home cannot be walked, is that `fail` (malware) or a third status?
  - A: `incomplete`, exit 2. The dashboard already treats any status other than `ok` or `fail` as attention, so this does not paint a false red malware row and does not paint green. `fail` stays "a pin or payload was found."

### 2026-11-22 — re-engineer
- Q: The parent `/home` can be scanned and green while a child home is never listed. What is the required home?
  - A: Each immediate child directory of `/home`. The parent walk does not count. No username is hardcoded. `--home` still replaces discovery. Operator instruction: scan the real home or take it as an argument. Recommended was the same, because a temp-tree repro showed `status=ok` and `pin_count=0` when the child mode was `000`.
- Q: What if `/home` has no child directories?
  - A: `incomplete`. An empty or unlistable parent is not a scanned home. Recommended was fail closed.

## Further Notes

- Constitution file is absent. Policy defaults: TDD, no secrets, bounded diff.
- `scripts/ops_dashboard.py` already maps non-ok, non-fail JSON to attention. No dashboard edit.
- Host `Path.home()` for the debian user is `/home/debian`. The bug appears when the unit's `User=root` sets the process home to `/root`.

## Handoff

- Next: `/execute_dev` (one sub-task; TDD)
- Then: `NEXT_SKILL` from `scripts/next_skill.py` (code review, behavior check if runtime)
- Then: `/pr_review --validate`
- Release and docs-sync only if those skills are required and they do not tag or push. This job forbids tag and push.
