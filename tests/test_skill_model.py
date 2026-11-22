"""Dispatch-level model pinning: declared in the skill, resolved by the dispatcher, reversible."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import skill_model  # noqa: E402


def _skill(root: Path, name: str, extra: str) -> None:
    d = root / ".agents" / "skills" / name
    d.mkdir(parents=True, exist_ok=True)
    (d / "SKILL.md").write_text(f"---\nname: {name}\n{extra}---\n\nbody\n", encoding="utf-8")


def test_declared_model_is_resolved(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("SKILL_MODEL_PIN", raising=False)
    _skill(tmp_path, "spec", "model: grok-4.7\nreasoning_effort: high\n")
    out = skill_model.resolve(tmp_path, "spec")
    assert out == {"skill": "spec", "model": "grok-4.7", "reasoning_effort": "high", "pinned": True}


def test_kill_switch_restores_old_behaviour(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SKILL_MODEL_PIN", "0")
    _skill(tmp_path, "spec", "model: grok-4.7\n")
    out = skill_model.resolve(tmp_path, "spec")
    assert out["pinned"] is False and out["model"] is None


def test_deterministic_step_declares_no_model(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("SKILL_MODEL_PIN", raising=False)
    _skill(tmp_path, "code_review", "model: none\n")
    out = skill_model.resolve(tmp_path, "code_review")
    assert out["deterministic"] is True and out["model"] is None


def test_undeclared_skill_is_unpinned(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("SKILL_MODEL_PIN", raising=False)
    _skill(tmp_path, "ad_hoc", "")
    assert skill_model.resolve(tmp_path, "ad_hoc")["pinned"] is False


def test_unavailable_model_fails_closed(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("SKILL_MODEL_PIN", raising=False)
    _skill(tmp_path, "spec", "model: gpt-9-imaginary\n")
    with pytest.raises(SystemExit) as exc:
        skill_model.resolve(tmp_path, "spec")
    assert "unavailable model" in str(exc.value)


def test_real_execute_dev_is_pinned() -> None:
    root = Path(__file__).resolve().parent.parent
    out = skill_model.resolve(root, "execute_dev")
    assert out["pinned"] is True and out["model"] in skill_model.ALLOWED
    json.dumps(out)
