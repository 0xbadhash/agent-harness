#!/usr/bin/env python3
"""When each harness/portfolio test runs — single SoT for OPS + night-shift logs.

Print markdown for embedding in OPS-DASHBOARD and product night-shift-log.md.
"""
from __future__ import annotations

# (phase, when_utc_hkt, what, where_visible, act_if_red)
ROWS: list[tuple[str, str, str, str, str]] = [
    (
        "Ship: /spec",
        "When you start a feature",
        "Spec path or Spec waiver; optional spec_sha256 pin",
        "PR_DRAFT + `.agents/specs/`",
        "Write AC-n before coding",
    ),
    (
        "Ship: /execute_dev",
        "During implementation",
        "TDD unit tests you write; product_smoke optional; property_tests if enabled in plugin",
        "Local terminal / pytest",
        "Keep suite green before review",
    ),
    (
        "Ship: /code_review",
        "After implement",
        "Human/agent CODE-REVIEW artifact (quality floor, not auto-stub)",
        "`.agents/artifacts/CODE_REVIEW.md`",
        "Expand review until hard_gates accept",
    ),
    (
        "Ship: /cross_review",
        "Large / multi-persona diffs",
        "CROSS-REVIEW evidence (soft unless --strict)",
        "`.agents/artifacts/CROSS_REVIEW.md`",
        "Add persona notes if required",
    ),
    (
        "Ship: /behavior_validator",
        "Runtime / public API surface",
        "BEHAVIOR-REPORT scenarios",
        "`.agents/artifacts/BEHAVIOR_REPORT.md`",
        "Cover AC runtime paths",
    ),
    (
        "Ship: /pr_review --validate",
        "Closeout before release",
        "J6 hard_gates: AC map, secrets, diff compile, path tests, red/green cmds, "
        "lockfile audit, threat tags, security_paths, property_tests, web_e2e; "
        "score ≥95 (suite, lint, §9, hardcodes)",
        "Terminal score JSON; fails ship",
        "Fix violations; never silent --skip-hard-gates without ALLOW_SKIP_HARD_GATES=1",
    ),
    (
        "Ship: /release_mgmt",
        "After approve",
        "Full smoke (+ web e2e if website); version/tag",
        "Git tags + product smoke",
        "Do not release if smoke fails",
    ),
    (
        "GitHub daytime-gates",
        "Every push/PR to main (minutes after push)",
        "CI smoke bar: hardcodes + smoke_ci + secrets (+ Semgrep warn)",
        "GitHub Actions tab per repo — **not** auto on OPS unless night also fails",
        "Open red run → fix → push",
    ),
    (
        "Night shift readiness",
        "~19:15 UTC daily (~03:15 HKT)",
        "Full product bar: hardcodes, validate, **full smoke** (heavier than CI), coverage, skills",
        "OPS-DASHBOARD Failing/Well + `01-Projects/<id>/night-shift-log.md` + TODO",
        "Open product TODO link; fix before next night",
    ),
    (
        "OPS-DASHBOARD refresh",
        "01:00 + 12:00 UTC (~09:00 + 20:00 HKT)",
        "Aggregates night, news, kanban, vault, security IoC, portfolio lag, waiver counts",
        "`agent-tasks/OPS-DASHBOARD.md`",
        "Act on Failing first, then Attention/To-do",
    ),
    (
        "ZAP baseline",
        "Weekly Mon 06:00 UTC (GitHub) + manual VPS",
        "Web DAST against catalyxt / watchlist / bip39 hosts (warn-only default)",
        "Harness `.agents/artifacts/zap/` — not ship-blocking yet",
        "Triage HIGH; keep header WARN accepted until CDN project",
    ),
    (
        "Weekly root IoC",
        "Sun ~04:30 UTC",
        "Root/containerd malware/IoC deep scan",
        "OPS security rows + security-ioc-status",
        "Isolate if FAIL",
    ),
]


def schedule_markdown(*, compact: bool = False) -> str:
    """Markdown block for OPS / night logs."""
    lines = [
        "## When tests run (act map)",
        "",
        "_SoT: `scripts/test_trigger_schedule.py` · ship chain + CI + night + ops._",
        "",
    ]
    if compact:
        lines.extend(
            [
                "| Phase | Clock | Tests | See | If red |",
                "|-------|-------|-------|-----|--------|",
            ]
        )
        for phase, when, what, where, act in ROWS:
            lines.append(
                f"| {phase} | {when} | {what} | {where} | {act} |"
            )
    else:
        lines.extend(
            [
                "| Phase / moment | When | What runs | Where you see it | If red — act |",
                "|----------------|------|-----------|------------------|--------------|",
            ]
        )
        for phase, when, what, where, act in ROWS:
            lines.append(
                f"| **{phase}** | {when} | {what} | {where} | {act} |"
            )
    lines.extend(
        [
            "",
            "### Ship chain order (human + agent)",
            "",
            "`/spec` → `/execute_dev` → `/code_review` → `/cross_review` (if large) "
            "→ `/behavior_validator` (if runtime) → `/pr_review --validate` → "
            "`/release_mgmt` → `/sync_docs`",
            "",
            "### Not the same as night",
            "",
            "- **GitHub green** = CI smoke_ci bar (fast).",
            "- **Night PASS** = VPS full readiness (validate + full smoke).",
            "- **OPS RED** = usually night fail, news, kanban, or security — open **Link** column.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--compact", action="store_true")
    args = ap.parse_args()
    print(schedule_markdown(compact=bool(args.compact)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
