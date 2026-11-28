"""Tests for the prototype contract, compact grill handoff, and plan data model.

Covers AC-2 from the top-50 completion spec.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import check_prototype_fidelity  # noqa: E402
import context_pack  # noqa: E402
import spec_gate  # noqa: E402


def _spec(
    tmp_path: Path,
    *,
    verdict: str = "variant a — least code",
    proto: str = ".agents/prototypes/slug",
    use: str = "reference",
) -> Path:
    path = tmp_path / ".agents" / "specs" / "demo.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "# Demo\n\n"
        f"**Prototype:** `{proto}`\n"
        f"**Prototype verdict:** {verdict}\n"
        f"**Prototype use:** {use}\n"
        "**Reserved decisions:** release\n"
        "**Delegated decisions:** names\n",
        encoding="utf-8",
    )
    return path


def _variants(tmp_path: Path, marker: bool = True) -> Path:
    base = tmp_path / ".agents" / "prototypes" / "slug"
    base.mkdir(parents=True)
    body = "# Prototype slug — variant a: simplest\n\n"
    if marker:
        body += "**DO NOT SHIP. Disposable sketch.**\n"
    (base / "variant-a.md").write_text(body, encoding="utf-8")
    (base / "variant-b.md").write_text(
        "# Prototype slug — variant b: inverted\n\n**DO NOT SHIP.**\n", encoding="utf-8"
    )
    return base


def test_no_prototype_is_fine(tmp_path: Path) -> None:
    spec = tmp_path / "spec.md"
    spec.write_text("**Prototype:** none\n", encoding="utf-8")
    ok, msgs = check_prototype_fidelity.check(tmp_path, spec=spec)
    assert ok, msgs


def test_recorded_prototype_passes(tmp_path: Path) -> None:
    spec = _spec(tmp_path)
    _variants(tmp_path)
    ok, msgs = check_prototype_fidelity.check(tmp_path, spec=spec)
    assert ok, msgs


def test_missing_verdict_fails(tmp_path: Path) -> None:
    spec = _spec(tmp_path, verdict="none")
    _variants(tmp_path)
    ok, msgs = check_prototype_fidelity.check(tmp_path, spec=spec)
    assert not ok
    assert any("Prototype verdict" in m for m in msgs)


def test_variant_without_do_not_ship_fails(tmp_path: Path) -> None:
    spec = _spec(tmp_path)
    _variants(tmp_path, marker=False)
    ok, msgs = check_prototype_fidelity.check(tmp_path, spec=spec)
    assert not ok
    assert any("DO NOT SHIP" in m for m in msgs)


def test_copied_prototype_code_fails(tmp_path: Path) -> None:
    spec = _spec(tmp_path)
    _variants(tmp_path)
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "cache.py").write_text(
        "# Prototype slug — variant a: simplest\ndef cache():\n    pass\n", encoding="utf-8"
    )
    ok, msgs = check_prototype_fidelity.check(tmp_path, spec=spec)
    assert not ok
    assert any("prototype code" in m for m in msgs)


def test_missing_prototype_use_fails(tmp_path: Path) -> None:
    spec = _spec(tmp_path, use="none")
    _variants(tmp_path)
    ok, msgs = check_prototype_fidelity.check(tmp_path, spec=spec)
    assert not ok
    assert any("Prototype use" in m for m in msgs)


def test_source_importing_prototypes_fails(tmp_path: Path) -> None:
    spec = _spec(tmp_path)
    _variants(tmp_path)
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "cache.py").write_text(
        "from prototypes.slug import cache\n", encoding="utf-8"
    )
    ok, msgs = check_prototype_fidelity.check(tmp_path, spec=spec)
    assert not ok
    assert any("imports the prototype" in m for m in msgs)


def test_prototype_must_live_under_prototypes(tmp_path: Path) -> None:
    spec = _spec(tmp_path, proto="scripts/sketch")
    (tmp_path / "scripts" / "sketch").mkdir(parents=True)
    ok, msgs = check_prototype_fidelity.check(tmp_path, spec=spec)
    assert not ok
    assert any("must live under .agents/prototypes" in m for m in msgs)


def test_compact_handoff_has_every_section(tmp_path: Path) -> None:
    spec = _spec(tmp_path)
    text = context_pack.build_grill_handoff(tmp_path, spec)
    for heading in (
        "## Decisions settled in the grill",
        "## Decision ownership",
        "## Glossary changes",
        "## ADR links",
        "## Prototype",
        "## Open questions",
    ):
        assert heading in text, heading
    assert "variant a" in text


def test_plan_template_has_data_model_and_deletion_policy() -> None:
    plan = (ROOT / "skills/spec/references/plan-template.md").read_text(encoding="utf-8")
    assert "## Data model" in plan
    assert "**Deletion policy:**" in plan


def test_data_model_term_must_resolve_in_glossary(tmp_path: Path) -> None:
    (tmp_path / "GLOSSARY.md").write_text(
        "| Term | Meaning |\n|---|---|\n| Ticket | unit of work |\n", encoding="utf-8"
    )
    plan = tmp_path / ".agents" / "specs" / "demo-plan.md"
    plan.parent.mkdir(parents=True)
    plan.write_text(
        "## Data model\n\n| Glossary term | Entity | Owner |\n|---|---|---|\n"
        "| Ticket | ticket | dag |\n\n**Deletion policy:** not-applicable\n",
        encoding="utf-8",
    )
    spec = tmp_path / ".agents" / "specs" / "demo.md"
    spec.write_text(f"**Plan:** `{plan.relative_to(tmp_path)}`\n", encoding="utf-8")
    ok, msgs = spec_gate.check_plan_data_model(tmp_path, spec.read_text())
    assert ok, msgs

    plan.write_text(
        "## Data model\n\n| Glossary term | Entity | Owner |\n|---|---|---|\n"
        "| Snapshot | snapshot | dag |\n\n**Deletion policy:** not-applicable\n",
        encoding="utf-8",
    )
    ok, msgs = spec_gate.check_plan_data_model(tmp_path, spec.read_text())
    assert not ok
    assert any("Snapshot" in m for m in msgs)


def test_spec_skill_names_research_and_modes() -> None:
    skill = (ROOT / "skills/spec/SKILL.md").read_text(encoding="utf-8")
    assert "read-only research subagent" in skill
    assert "--mode batch" in skill and "--mode serial" in skill
    assert "RESEARCH_NOTES.md" in skill
    assert "prototype_variants.py" in skill


def test_prototype_skill_states_reference_rule() -> None:
    skill = (ROOT / "skills/prototype/SKILL.md").read_text(encoding="utf-8")
    assert "never the implementation" in skill
    assert "check_prototype_fidelity.py" in skill
