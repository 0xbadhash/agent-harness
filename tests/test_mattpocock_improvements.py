"""Tests for deterministic harness improvements (AC-1 through AC-7)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))


def test_ac1_diagnosing_bugs_skill_and_debug_tag_gate(tmp_path: Path) -> None:
    skill = ROOT / "skills" / "diagnosing-bugs" / "SKILL.md"
    assert skill.is_file(), "skills/diagnosing-bugs/SKILL.md missing"
    text = skill.read_text(encoding="utf-8")
    assert "[DEBUG-" in text and "red" in text.lower()

    import check_repo_hygiene

    bad = tmp_path / "app.py"
    bad.write_text('print("[DEBUG-a4f2] leak")\n', encoding="utf-8")
    fails = check_repo_hygiene.scan_debug_tags(tmp_path)
    assert fails == 1


def test_ac2_two_axis_code_review() -> None:
    cr = (ROOT / "skills" / "code_review" / "SKILL.md").read_text(encoding="utf-8")
    assert "## Standards" in cr and "## Spec" in cr
    import hard_gates

    has_axes, detail = hard_gates.check_code_review_axes("## Standards\nnone\n## Spec\nnone\n")
    assert has_axes is True, detail
    missing_axes, _ = hard_gates.check_code_review_axes("just some text")
    assert missing_axes is False


def test_ac3_merge_danger_template_and_validator() -> None:
    tpl = (ROOT / "templates" / "PR_DRAFT.md").read_text(encoding="utf-8")
    assert "## Merge Danger" in tpl
    assert "**Door:**" in tpl
    assert "**Blast Radius:**" in tpl

    import pr_validator

    ok, msg = pr_validator.validate_merge_danger(
        "## Merge Danger\n**Door:** two-way\n**Blast Radius:** local\n"
    )
    assert ok is True, msg
    bad_ok, _ = pr_validator.validate_merge_danger("## Merge Danger\n**Door:** one-way\n")
    assert bad_ok is False


def test_ac4_verify_skills_style_lint(tmp_path: Path) -> None:
    import verify_skills

    sdir = tmp_path / ".agents" / "skills" / "bloated"
    sdir.mkdir(parents=True)
    long_desc = "x" * 260
    body = "\n".join(f"line {i}" for i in range(220))
    (sdir / "SKILL.md").write_text(
        f"---\nname: bloated\ndescription: {long_desc}\ndisable-model-invocation: true\n---\n{body}\n",
        encoding="utf-8",
    )
    warns = verify_skills.check_skill_style(sdir / "SKILL.md")
    assert len(warns) >= 2


def test_ac5_retrospect_and_agents_bloat(tmp_path: Path) -> None:
    retro = (ROOT / "skills" / "retrospect" / "SKILL.md").read_text(encoding="utf-8")
    assert "mechanical" in retro.lower()

    import check_stale_agent_config

    agents_md = tmp_path / "AGENTS.md"
    agents_md.write_text("\n".join(f"rule {i}" for i in range(260)), encoding="utf-8")
    warns = check_stale_agent_config.check_agents_bloat(tmp_path)
    assert len(warns) == 1


def test_ac6_ticket_dag_frontier_and_cycle(tmp_path: Path) -> None:
    dag_script = ROOT / "scripts" / "check_ticket_dag.py"
    assert dag_script.is_file(), "scripts/check_ticket_dag.py missing"

    t1 = tmp_path / "01-a.md"
    t2 = tmp_path / "02-b.md"
    t1.write_text("# 01: A\n**Blocked by:** None\n**Status:** ready-for-agent\n", encoding="utf-8")
    t2.write_text("# 02: B\n**Blocked by:** 01\n**Status:** ready-for-agent\n", encoding="utf-8")

    r = subprocess.run(
        [sys.executable, str(dag_script), str(tmp_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 0, r.stderr
    assert "01" in r.stdout

    # Cycle must fail closed
    t1.write_text("# 01: A\n**Blocked by:** 02\n**Status:** ready-for-agent\n", encoding="utf-8")
    r_cyc = subprocess.run(
        [sys.executable, str(dag_script), str(tmp_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert r_cyc.returncode == 1


def test_ac7_glossary_references() -> None:
    spec_md = (ROOT / "skills" / "spec" / "SKILL.md").read_text(encoding="utf-8")
    exec_md = (ROOT / "skills" / "execute_dev" / "SKILL.md").read_text(encoding="utf-8")
    assert "GLOSSARY.md" in spec_md
    assert "GLOSSARY.md" in exec_md
