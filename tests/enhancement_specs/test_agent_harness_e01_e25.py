"""Enhancement specs 1-25: agent-harness.

Each test = deterministic acceptance test for one numbered enhancement from
reports/50-ENHANCEMENTS-HARNESSES-2026-11-22.md. Red now means pending.
"""
from __future__ import annotations

import re

from conftest import AH, ah, must_contain, src, text_of

GATE_SCRIPTS = [
    "spec_gate.py", "hard_gates.py", "check_waiver_budget.py", "check_spec_hash.py",
    "check_spec_grill.py", "check_ac_traceability.py", "check_changed_path_tests.py",
    "check_outer_loop.py", "run_ship_chain.py", "start_feature.py",
]


# E01 — single source of gate conventions
def test_e01_gate_conventions_single_source():
    mod = ah("scripts", "gate_conventions.py")
    must_contain(mod, "Spec:")
    body = text_of(mod)
    assert re.search(r"SPEC(_| ).{0,20}(RE|Pattern)|SPEC_PATTERN", body), "gate_conventions.py must expose the spec patterns as importable constants"
    for s in GATE_SCRIPTS:
        p = ah("scripts", s)
        if p.is_file():
            assert "gate_conventions" in src(p), f"{s} still re-declares gate conventions instead of importing gate_conventions"
    # no other script may inline the waiver regex any more
    dupes = [s.name for s in AH.joinpath("scripts").glob("*.py")
             if s.name != "gate_conventions.py" and re.search(r"\*\*Spec waiver:\*\*", src(s))]
    assert not dupes, f"inline spec-waiver patterns remain in: {dupes}"


# E02 — coverage thresholds enforced in CI
def test_e02_coverage_in_ci():
    ci = text_of(AH.joinpath(".github", "workflows", "daytime-gates.yml"))
    assert "coverage" in ci.lower(), "daytime-gates.yml must run coverage"
    assert "check_module_coverage" in ci, "CI must invoke the module-coverage gate"


# E03 — fork-drift alarm in the daytime status script
def test_e03_fork_drift_alarm():
    body = src(AH.joinpath("scripts", "github_daytime_status.py"))
    assert re.search(r"ahead|behind", body), "status script must compare local main to origin/main"
    assert re.search(r"page|alert|notify|fail|red", body, re.I), "drift must escalate, not stay silent"


# E04 — the harness ships through its own ship chain
def test_e04_dogfood_ship_chain():
    body = src(AH.joinpath("scripts", "run_ship_chain.py"))
    assert re.search(r"--self|ship[_-]self|self[_-]ship|SHIP_SELF", body), \
        "run_ship_chain must expose an explicit self-ship path for the harness repo itself"


# E05 — missing tool => DEGRADED, not skip
def test_e05_missing_tool_is_degraded():
    ns = src(AH.joinpath("scripts", "night_shift_readiness.py"))
    assert "DEGRADED" in ns, "night shift must emit a DEGRADED verdict for missing required tools"
    assert re.search(r"required[_-]tools|tool[_-]manifest", ns, re.I), \
        "a per-product required-tools manifest must drive the verdict"


# E06 — suite-did-not-run surfaces as RED_SUITE, not skip
def test_e06_red_suite_status():
    hit = [p.read_text(errors="replace") for p in AH.joinpath("scripts").glob("*.py")
           if "RED_SUITE" in p.read_text(errors="replace")]
    assert hit, "no gate surfaces a distinct RED_SUITE status; suite-not-run must not fold into skip"


# E07 — night_shift_all_products split into library + thin CLI
def test_e07_night_shift_split():
    cli = AH.joinpath("bin", "night_shift_all_products.py")
    lines = len(text_of(cli).splitlines())
    assert lines <= 400, f"night_shift_all_products.py is still {lines} lines (target <=400 after lib split)"
    lib = list(AH.joinpath("scripts").glob("night_shift*.py"))
    assert any("lib" in p.name or "core" in p.name or "engine" in p.name for p in lib), \
        "a night-shift library module must exist"


# E08 — property-based tests for the gate parsers
def test_e08_property_tests_for_parsers():
    reqs = text_of(AH.joinpath("requirements-dev.txt"))
    assert "hypothesis" in reqs, "hypothesis must be a dev dependency"
    prop_tests = list(AH.joinpath("tests").glob("test_*propert*.py")) + list(AH.joinpath("tests").glob("test_*hypothesis*.py"))
    assert prop_tests, "property-based tests for gate parsers must exist under tests/"
    for p in prop_tests:
        assert "hypothesis" in src(p), f"{p.name} must actually use hypothesis"


# E09 — PR-body format gate
def test_e09_pr_body_gate():
    p = ah("scripts", "check_pr_body.py")
    must_contain(p, "smallest")
    body = src(p)
    assert "one-way" in body and "two-way" in body, "PR gate must require a merge-danger call"


# E10 — two-axis code review
def test_e10_two_axis_review():
    body = src(AH.joinpath("scripts", "cross_review_gate.py"))
    assert "standards" in body.lower() and ("spec" in body.lower()), \
        "cross review must run separate standards and spec-fidelity axes"


# E11 — ratcheting lint with a checked-in baseline
def test_e11_ratcheting_lint():
    # a ratchet needs a baseline DATA file (per-rule counts) AND a checker that
    # reads it; ZAP security-baseline files are unrelated and excluded.
    data = [p for p in AH.rglob("*baseline*")
            if p.suffix in {".json", ".toml", ".yaml", ".yml"} and "zap" not in p.name.lower()
            and ".agents" not in p.parts and ".github" not in p.parts]
    assert data, "no lint-ratchet baseline data file exists (per-rule violation counts)"
    checker_hits = [p.name for p in AH.joinpath("scripts").glob("*.py")
                    if data[0].name in p.read_text(errors="replace")]
    assert checker_hits, "no checker consumes the ratchet baseline"


# E12 — post-ship retro job
def test_e12_retro_job():
    assert ah("scripts", "retro_job.py").is_file() or ah("scripts", "ship_retro.py").is_file(), \
        "a retro job script must exist (session transcripts + review comments -> ratcheted checks)"


# E13 — ADR three-part test in the spec gate
def test_e13_adr_three_part_test():
    body = src(AH.joinpath("scripts", "spec_gate.py"))
    assert re.search(r"reversib", body, re.I), "spec gate must test the ADR reversibility clause"
    assert re.search(r"surpris", body, re.I), "spec gate must test the surprise clause"
    assert re.search(r"tradeoff|trade-off", body, re.I), "spec gate must test the tradeoff clause"


# E14 — glossary enforcement in the spec gate
def test_e14_glossary_enforced():
    assert "GLOSSARY" in src(AH.joinpath("scripts", "spec_gate.py")), \
        "spec gate must check undefined domain terms against GLOSSARY.md"


# E15 — comment audit gate
def test_e15_comment_audit_gate():
    audit = [p for p in AH.joinpath("scripts").glob("*comment*")]
    assert audit, "a comment-audit gate/classifier must exist"


# E16 — tracer-bullet tickets with blocking edges
def test_e16_ticket_blocking_edges():
    body = src(AH.joinpath("scripts", "spec_gate.py")) + src(AH.joinpath("scripts", "start_feature.py"))
    assert re.search(r"depends_on|blocked[_-]by|blocks:", body), \
        "tickets must declare blocking edges and the gate must require them"


# E17 — diff-sizing decision tree at window open
def test_e17_diff_sizing_tree():
    body = src(AH.joinpath("scripts", "start_feature.py"))
    for level in ("small", "medium", "huge"):
        assert level in body.lower(), f"start_feature must classify diff size: missing {level}"


# E18 — smart-zone token guard for implementer subagents
def test_e18_smart_zone_guard():
    hay = "\n".join(p.read_text(errors="replace") for p in AH.joinpath("scripts").glob("*.py"))
    assert re.search(r"150[_\s,]*000|150k", hay), "a ~150k token smart-zone budget must be encoded"
    assert re.search(r"externaliz", hay, re.I), "past the budget, state must be externalized to artifacts"


# E19 — compact-safety gate
def test_e19_compact_safety_gate():
    p = ah("scripts", "check_compact_safety.py")
    body = src(p)
    assert "spec" in body.lower() and ("ticket" in body.lower() or "glossary" in body.lower()), \
        "compaction must be blocked until spec/tickets/glossary are on disk"


# E20 — reproduction harness requirement for bug fixes
def test_e20_repro_required_for_bugfixes():
    body = src(AH.joinpath("scripts", "spec_gate.py")) + src(AH.joinpath("scripts", "check_red_green_cmds.py"))
    assert re.search(r"repro", body, re.I), "bug-fix specs must require a repro that went red first"


# E21 — waiver root-cause clustering
def test_e21_waiver_clustering():
    body = src(AH.joinpath("scripts", "waiver_report.py"))
    assert re.search(r"cluster|group[_-]by", body, re.I), "waiver_report must cluster repeated waivers by gate"


# E22 — prototype variants for design questions
def test_e22_prototype_variants():
    p = ah("scripts", "prototype_variants.py")
    if p.is_file():
        return
    grill = src(AH.joinpath("scripts", "check_spec_grill.py"))
    assert re.search(r"prototype", grill, re.I), \
        "the grill must drive disposable prototype variants for design questions"


# E23 — wizard generator for CEO-only steps
def test_e23_wizard_generator():
    assert ah("scripts", "wizard.py").is_file() or any(AH.joinpath("skills").glob("*wizard*")), \
        "a wizard generator for human-only provisioning steps must exist"


# E24 — research skill producing cited repo artifacts
def test_e24_research_skill():
    cand = list(AH.joinpath("skills").glob("*research*")) + list(AH.joinpath("scripts").glob("*research*"))
    assert cand, "a research skill/script must exist (cited markdown into the repo)"


# E25 — fork sync bot
def test_e25_fork_sync_bot():
    p = ah("scripts", "fork_sync_bot.py")
    body = src(p)
    assert re.search(r"issue", body, re.I), "divergence must open a tracker issue, not stay silent"
